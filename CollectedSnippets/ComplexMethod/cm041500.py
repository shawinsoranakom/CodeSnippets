def test_last_updated_date(self, secret_name, aws_client):
        # TODO: moto is rounding time.time() but `secretsmanager`return a timestamp with 3 fraction digits
        # adapt the tests for around equality
        aws_client.secretsmanager.create_secret(Name=secret_name, SecretString="MySecretValue")

        res = aws_client.secretsmanager.describe_secret(SecretId=secret_name)
        assert "LastChangedDate" in res
        create_date = res["LastChangedDate"]
        assert isinstance(create_date, datetime)
        create_date_ts = create_date.timestamp()

        res = aws_client.secretsmanager.get_secret_value(SecretId=secret_name)
        assert isclose(create_date_ts, res["CreatedDate"].timestamp(), rel_tol=1)

        res = aws_client.secretsmanager.describe_secret(SecretId=secret_name)
        assert "LastChangedDate" in res
        assert isclose(create_date_ts, res["LastChangedDate"].timestamp(), rel_tol=1)

        aws_client.secretsmanager.update_secret(
            SecretId=secret_name, SecretString="MyNewSecretValue"
        )

        res = aws_client.secretsmanager.describe_secret(SecretId=secret_name)
        assert "LastChangedDate" in res
        assert create_date < res["LastChangedDate"]
        last_changed = res["LastChangedDate"]

        aws_client.secretsmanager.update_secret(
            SecretId=secret_name, SecretString="MyNewSecretValue"
        )

        res = aws_client.secretsmanager.describe_secret(SecretId=secret_name)
        assert "LastChangedDate" in res
        assert last_changed < res["LastChangedDate"]

        aws_client.secretsmanager.update_secret(
            SecretId=secret_name, SecretString="MyVeryNewSecretValue"
        )

        res = aws_client.secretsmanager.describe_secret(SecretId=secret_name)
        assert "LastChangedDate" in res
        assert create_date < res["LastChangedDate"]