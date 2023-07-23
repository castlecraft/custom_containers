## Continuous Deployment on Docker Swarm

### Pull deployment

Use portainer to add a stack using file located on a git repository. It will watch for that repo for the change to the stack yaml and apply changes.

### Push deployment

Create stacks under portainer, for each service in a stack create a webhook to update the service. From CI job make a POST request using `curl` to the webhook url generated on portainer.

## Continuous Deployment on Kubernetes

### Prerequisites

You need your custom `values.yaml` containing ONLY the keys that are to be overridden. DO NOT copy full `values.yaml` it will be difficult to determine which key was overridden in that case just by looking at the `values.yaml`.

### Pull deployment

In case of pull deployment you need gitops operator like FluxCD. You will commit changes in `values.yaml` to a gitops repository and it will generate a release out of those values on your cluster.

### Push deployment

In case of push deployment your CI runner has the access to you cluster and it will run `helm upgrade` command with changes to the overridden `values.yaml` available in the repo at the time of CI job execution.
