## Getting Started for Enterprise

- Access to a git repo designated as `project_builds`.
- One repo for frappe app that hosts business specific customization `project_custom`
- One container registry. e.g. ghcr.io, registry.gitlab.com
- CI Runner tool and minutes of runtime on them, e.g. GitHub Actions, Gitlab Runner, Circle CI, etc
- Components for setting up one environment
    - VM with minimun 2 vCPU and 4GB RAM
    - S3 compatible Object Storage to push daily backups
    - Optionally NFS server or managed NAS, e.g. AWS EFS
    - Optionally MariaDB server or managed DB, e.g. AWS RDS
    - Container Registrt
- Setup at least one production and one staging environment
- Start with Docker Swarm. If Volume and Database is separate then the same services can be transfered to Kubernetes and docker swarm can stop serving the load.
