def test_create_multi_secrets(self, cleanups, aws_client):
        secret_names = [short_uid(), short_uid(), short_uid()]
        arns = []
        for secret_name in secret_names:
            cleanups.append(
                lambda: aws_client.secretsmanager.delete_secret(
                    SecretId=secret_name, ForceDeleteWithoutRecovery=True
                )
            )
            rs = aws_client.secretsmanager.create_secret(
                Name=secret_name,
                SecretString=f"my_secret_{secret_name}",
                Description="testing creation of secrets",
            )
            arns.append(rs["ARN"])
            self._wait_created_is_listed(aws_client.secretsmanager, secret_id=secret_name)

        rs = aws_client.secretsmanager.get_paginator("list_secrets").paginate().build_full_result()
        secrets = {
            secret["Name"]: secret["ARN"]
            for secret in rs["SecretList"]
            if secret["Name"] in secret_names
        }

        assert len(secrets.keys()) == len(secret_names)
        for arn in arns:
            assert arn in secrets.values()

        # clean up
        for secret_name in secret_names:
            aws_client.secretsmanager.delete_secret(
                SecretId=secret_name, ForceDeleteWithoutRecovery=True
            )