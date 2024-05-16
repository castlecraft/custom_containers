### Add to kerberos

In `kerberos` container:

```shell
kadmin.local -q 'addprinc -x dn=cn=Posix" "User,ou=Users,dc=example,dc=com posix.user'
```

In `development` container:

```shell
wait-for-it kerberos:749

kadmin -p admin -q "addprinc -randkey HTTP/localhost" <<EOF
admin
admin
EOF

sudo kadmin -p admin -q "ktadd HTTP/localhost" <<EOF
admin
admin
EOF

sudo chown -R vscode:root /etc/krb5.keytab

kinit -k HTTP/localhost

klist
```
