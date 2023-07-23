### Migrate from VM to containers using rsync

Use the script to migrate a site from VM to container based setup using `ssh` and `rsync` installed in container.

The following script requires `ssh` and `rsync` installed in your image.

Execute following command using `scripts/migratevm.py` to know more about command,

```shell
python sites/migratevm.py --help

usage: migration [-h] --vm-user VM_USER --vm-host VM_HOST --db-host DB_HOST --db-root-user DB_ROOT_USER --db-root-password
                 DB_ROOT_PASSWORD --bench-dir BENCH_DIR --site SITE [--dest-dir DEST_DIR] [--dest-bench DEST_BENCH]
                 [--keyfile-path KEYFILE_PATH] [--dbaas] [--no-pause] [--restore-remotely] [--clear-db-host]

optional arguments:
  -h, --help            show this help message and exit
  --vm-user VM_USER     user on vm with ssh access
  --vm-host VM_HOST     ip or hostname of vm
  --db-host DB_HOST     db host
  --db-root-user DB_ROOT_USER
                        db root user
  --db-root-password DB_ROOT_PASSWORD
                        db root password
  --bench-dir BENCH_DIR
                        source bench dir
  --site SITE           name of site to be copied
  --dest-dir DEST_DIR   site directory on destination
  --dest-bench DEST_BENCH
                        destination bench dir
  --keyfile-path KEYFILE_PATH
                        site directory on destination
  --dbaas               set if using DBaaS
  --no-pause            Do not pause source site
  --restore-remotely    restore from vm
  --clear-db-host       Clear db_host from site_config.json
```

Example:

```shell
migratevm.py \
 --dbaas \
 --vm-user=ubuntu \
 --vm-host=ec2-12-34-56-78.compute-1.amazonaws.com \
 --db-host=database.random.us-east-1.rds.amazonaws.com \
 --db-root-user=root \
 --db-root-password="changeit" \
 --bench-dir=/home/frappe/frappe-bench \
 --site=erp.example.com \
 --keyfile-path=/home/frappe/.ssh/id_rsa \
 --no-pause \
 --restore-remotely
```
