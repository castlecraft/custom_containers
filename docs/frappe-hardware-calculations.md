## 1. Capacity Planning: The 75% / 10% User Assumption

To accurately size your Kubernetes nodes and Database clusters, we must calculate the expected concurrent load. We will use standard enterprise software assumptions:

*   **Active Users (75%):** Of your total provisioned users, 75% log in and use the system during a typical business day.
*   **Concurrent Users (10%):** Of the active users, 10% are strictly concurrent (clicking, saving, or generating reports at the *exact same second*).

**Mathematical Model:**
```math
\text{Concurrent Users} = (\text{Total Users} \times 0.75) \times 0.10
```

*Example for 1,000 Total Users:*
*   Active Users = 750
*   Concurrent Users = 75

Since each Gunicorn pod handles 8 concurrent threads, and users do not hold connections open endlessly (they click, wait, read), a single Gunicorn pod can typically support roughly 15-20 *concurrently active* users.

---

## 2. Kubernetes Cluster Sizing Recommendations

### Baseline Resource Footprint (Per Environment)

Before sizing for user concurrency, you must account for the base resource consumption of a complete Frappe deployment. A standard unscaled environment (1 replica of each component) requires roughly **~0.5 vCPU and ~1 GB RAM** at idle, distributed across the following essential pods:

*   **Gunicorn (Web Workers):** ~400Mi RAM / 2m CPU base (scales heavily with concurrent users)
*   **Background Workers (Default, Long, Short queues):** ~75Mi RAM / 50-125m CPU *each*
*   **Scheduler:** ~75Mi RAM / 100m CPU
*   **SocketIO (Real-Time Updates):** ~50Mi RAM / 2m CPU
*   **Nginx (Web Server):** ~5Mi RAM / 1m CPU
*   **Redis (Cache & Queue):** ~110Mi RAM / 100m CPU combined

### Application Tier Node Sizing

Based on the baseline resources and the user behavior assumptions above, here is the recommended sizing for the Kubernetes worker nodes hosting the Application Tier. While Gunicorn handles HTTP traffic, you must also scale Background Workers (for reports, emails, webhooks) and SocketIO (for real-time websocket connections).

*Note: In production, always spread workloads across a minimum of 3 worker nodes for High Availability (HA).*

| Tier / Total Users | Assumed Concurrent Users | Recommended Replicas (Gunicorn / Workers / SocketIO) | Recommended K8s Node Size (App Tier) | Minimum Node Count |
| :--- | :--- | :--- | :--- | :--- |
| **Small (< 250)** | ~20 | 2 / 1 per queue / 1 | 2 vCPU / 8 GB RAM | 3 Nodes |
| **Medium (250 - 1,000)** | ~75 | 4 - 6 / 2 per queue / 1 | 4 vCPU / 16 GB RAM | 3 Nodes |
| **Large (1,000 - 5,000)** | ~375 | 15 - 25 / 4 - 8 per queue / 1 | 8 vCPU / 32 GB RAM | 3 - 5 Nodes |
| **Enterprise (5,000+)** | 375+ | HPA (20+ / 10+ / 1) | 16 vCPU / 64 GB RAM | 5+ Nodes |

**Important K8s Sizing Notes:**
*   **Gunicorn Scaling:** Handled best by a Horizontal Pod Autoscaler (HPA) targeting ~600Mi average memory.
*   **Worker Scaling:** Background workers (Long, Short, Default queues) should be scaled up based on the volume of scheduled jobs and API integrations, independent of direct user concurrency. Consider using KEDA to scale based on Redis queue length.
*   **SocketIO Scaling:** SocketIO requires sticky sessions to function correctly. Without complex ingress controller configurations, scaling beyond 1 pod will break real-time updates. It is highly recommended to **keep SocketIO at exactly 1 pod**. If it hits resource limits under heavy load, you must vertically scale it (increase CPU/RAM requests and limits) instead of adding replicas.
*   **Cluster Autoscaler:** Ensure it is enabled alongside HPA. If the HPA requests more pods than the current nodes can support (due to memory limits), the cluster autoscaler will provision new underlying VMs.
*   When scaling or adding new environments, remember that each environment brings its own baseline footprint. The cluster must have enough capacity for both the scaled Gunicorn pods and the fixed supporting pods (Workers, Scheduler, SocketIO, Redis).

---

## 3. MariaDB Cluster Sizing Recommendations

The database tier is often the ultimate bottleneck for ERPNext. Frappe is highly reliant on database performance. MariaDB relies heavily on the **InnoDB Buffer Pool**, which caches table data and indexes in RAM. As a rule of thumb, the buffer pool should fit your active dataset and consume roughly **70-80% of the total Database Server RAM**.

For production, deploy MariaDB in a High Availability setup (e.g., Galera Cluster with 3 nodes, or Primary-Replica architectures).

| Tier / Total Users | Assumed Concurrent Load | DB vCPU Per Node | DB RAM Per Node | Storage Type | Architecture |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Small (< 250)** | Light (mostly reads) | 4 vCPU | 8 GB - 16 GB | SSD / NVMe | Primary + 1 Replica |
| **Medium (250 - 1,000)**| Moderate | 8 vCPU | 32 GB - 64 GB | NVMe (High IOPS) | Galera (3-Node) or Primary/Replica |
| **Large (1,000 - 5,000)**| Heavy Reporting / Writes | 16 vCPU | 128 GB | NVMe (Provisioned IOPS)| Galera (3-Node) |
| **Enterprise (5,000+)** | Extreme / API Heavy | 32+ vCPU | 256 GB+ | Enterprise SAN/NVMe | Dedicated DB Cluster / Sharding considerations |

**Database Tuning Best Practices for ERPNext:**
1.  `innodb_buffer_pool_size`: Set to 70%-80% of the total RAM.
2.  `innodb_buffer_pool_instances`: Set to 1 for every 1GB of buffer pool size (e.g., if pool is 16GB, instances = 16).
3.  `max_connections`: Must be sized to handle the maximum potential pods. Formula:
    ```math
    \text{Max DB Connections} > (\text{Max Gunicorn Pods} \times \text{Workers} \times \text{Threads}) + \text{Background Workers} + \text{Buffer}
    ```

## 4. Additional Architecture & Deployment Considerations

*   **The "YMMV" Rule (Your Mileage May Vary):** Not all concurrent users load the system equally; ERPNext modules have vastly different computational weights. For instance, 100 concurrent users doing simple data entry in CRM will consume significantly fewer resources than 100 users running heavy API syncs, executing complex Manufacturing routings, or generating massive Stock Ledger reports. Always monitor actual CPU/Memory usage to fine-tune your specific baseline.
*   **Kubernetes Storage Classes (`ReadWriteMany`):** When deploying on K8s, Frappe requires a **`ReadWriteMany` (RWX)** storage class for the `sites` volume. Standard cloud block storage is typically `ReadWriteOnce` (RWO) and cannot be mounted across multiple pods. You must use an RWX solution (such as **NFS, AWS EFS, or CephFS**) to ensure all Gunicorn and Background Worker pods can simultaneously read and write to the same uploaded files and public/private assets.
*   **Redis Separation (Enterprise Tiers):** As your user base grows, it is highly recommended to split your Redis architecture into two separate instances: **Redis Cache** and **Redis Queue**. Redis Cache is highly volatile and uses eviction policies when full. If your job queues share the same instance, a sudden cache overflow could result in Redis automatically dropping critical background jobs, scheduled tasks, or webhooks before they have a chance to execute.
