def test_secret_exists(self, secret_name, aws_client):
        description = "Testing secret already exists."
        rs = aws_client.secretsmanager.create_secret(
            Name=secret_name,
            SecretString=f"my_secret_{secret_name}",
            Description=description,
        )
        self._wait_created_is_listed(aws_client.secretsmanager, secret_id=secret_name)
        secret_arn = rs["ARN"]
        secret_id = rs["Name"]
        assert len(secret_arn.rpartition("-")[-1]) == 6

        ls = aws_client.secretsmanager.get_paginator("list_secrets").paginate().build_full_result()
        secrets = {
            secret["Name"]: secret["ARN"]
            for secret in ls["SecretList"]
            if secret["Name"] == secret_name
        }
        assert len(secrets.keys()) == 1
        assert secret_arn in secrets.values()

        with pytest.raises(
            aws_client.secretsmanager.exceptions.ResourceExistsException
        ) as res_exists_ex:
            aws_client.secretsmanager.create_secret(
                Name=secret_name,
                SecretString=f"my_secret_{secret_name}",
                Description=description,
            )
        assert res_exists_ex.typename == "ResourceExistsException"
        assert res_exists_ex.value.response["ResponseMetadata"]["HTTPStatusCode"] == 400
        assert (
            res_exists_ex.value.response["Error"]["Message"]
            == f"The operation failed because the secret {secret_id} already exists."
        )