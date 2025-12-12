## The Scaling Situation: Why the Frappe Pod Slows Down

The slowdown observed—requests queuing, high memory use, and slow response times under heavy load—is a case of **resource exhaustion** under a thread-based application architecture (Gunicorn using the `gthread` worker class).

### The Core Problem: Hitting Concurrency Limits

The pod's current Gunicorn configuration sets a hard limit on simultaneous work:

| Component | Setting | Total Capacity |
| :--- | :--- | :--- |
| **Workers (Processes)** | 2 | |
| **Threads (Per Worker)**| 4 | |
| **Total Concurrent Requests** | $2 \times 4$ | **8 concurrent requests** |

1.  **High Load Arrives:** When a sudden influx of requests exceeds **8**, the available threads are immediately consumed.
2.  **Requests Queue:** All subsequent requests are forced to **wait in a queue**. This waiting time is what users experience as **slowness** and potential time-outs.
3.  **Memory Spikes:** Python/Frappe applications are **memory-intensive**. The active requests (up to 8) load data and context into memory simultaneously. Even the **queued requests** consume some memory while waiting. This cumulative memory usage quickly spikes, acting as a crucial indicator that the pod is overwhelmed.

In short, the pod **ran out of capacity (threads)**, which caused a queue, and the intense, concurrent processing led to **memory exhaustion**.

---

## The Solution: Horizontal Pod Autoscaler (HPA)

Using the **Horizontal Pod Autoscaler (HPA)** set to trigger at **600MB Average Memory**—is the standard and most effective solution to this scaling bottleneck.

| HPA Action | Effect | Outcome |
| :--- | :--- | :--- |
| **Trigger Metric** | $\mathbf{600\text{MB}}$ Average Memory | As the pod hits this ceiling (due to high request volume), the HPA is instantly alerted. |
| **Scaling Action** | HPA provisions **new pods** | New, identical Frappe pods are automatically created (e.g., scaling from 1 to 2 pods). |
| **Result** | **Doubled Capacity** | The total capacity doubles (e.g., from 8 to 16 concurrent requests). Queued requests are immediately distributed to the new pods, ensuring **zero slowdown**. |

### Why Memory is the Right Metric

In Python-based systems like Frappe, **Memory** is the fastest and most reliable **leading indicator of load**. We scale based on memory because:
* It's the first resource to hit a critical limit when many processes are active.
* It allows for **preventive scaling**—we add capacity *before* the pod runs out of memory, crashes, or user-facing performance degrades severely.

## Allocate Resources

### Resource Usage

This table shows average memory consumption for each pod when the system is not under heavy load. The second column is an approximation (likely **Current Usage** or **Current Request Count**), and the third column is the **Memory Usage**.

| Pod Name | CPU (cores) | Memory (bytes) | Component Role |
| :--- | :--- | :--- | :--- |
| **frappe-bench-erpnext-gunicorn** | **2m** | **400Mi** | **Web Workers** (Handles user HTTP requests) |
| frappe-bench-erpnext-nginx | 1m | 5Mi | **Web Server** (Handles static assets/routing) |
| frappe-bench-erpnext-scheduler | 100m | 75Mi | **Scheduler** (Manages time-based tasks/cron) |
| frappe-bench-erpnext-socketio | 2m | 50Mi | **Real-Time Updates** (Live events/notifications) |
| frappe-bench-erpnext-worker-d | 50m | 75Mi | **Background Worker (Default Queue)** |
| frappe-bench-erpnext-worker-l | 125m | 75Mi | **Background Worker (Long Queue)** |
| frappe-bench-erpnext-worker-s | 100m | 75Mi | **Background Worker (Short Queue)** |
| frappe-bench-redis-cache-master | 50m | 100Mi | **Redis Cache** (Fast data storage for sessions/cache) |
| frappe-bench-redis-queue-master | 50m | 10Mi | **Redis Queue** (Stores jobs for background workers) |

---

Note:

- If additional frappe benches (Helm Releases) are added, make sure appropriate resources are provisioned.
- In production each pod is replicated, make sure appropriate resources are available, resize nodes or resize number of nodes in the cluster to allocate the required resources.
