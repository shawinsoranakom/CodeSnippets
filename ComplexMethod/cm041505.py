def last_accessed_scenario_1(fail_if_days_overlap: bool) -> bool:
            secret_name = f"s-{short_uid()}"
            cleanups.append(
                lambda: aws_client.secretsmanager.delete_secret(
                    SecretId=secret_name, ForceDeleteWithoutRecovery=True
                )
            )

            aws_client.secretsmanager.create_secret(Name=secret_name, SecretString="MySecretValue")

            des = aws_client.secretsmanager.describe_secret(SecretId=secret_name)
            assert "LastAccessedDate" not in des

            t0 = today_no_time()

            aws_client.secretsmanager.get_secret_value(SecretId=secret_name)
            des = aws_client.secretsmanager.describe_secret(SecretId=secret_name)
            assert "LastAccessedDate" in des
            lad_v0 = des["LastAccessedDate"]
            assert isinstance(lad_v0, datetime)

            aws_client.secretsmanager.get_secret_value(SecretId=secret_name)
            des = aws_client.secretsmanager.describe_secret(SecretId=secret_name)
            assert "LastAccessedDate" in des
            lad_v1 = des["LastAccessedDate"]
            assert isinstance(lad_v1, datetime)

            if t0 == today_no_time() or fail_if_days_overlap:
                assert lad_v0 == lad_v1
                return True
            else:
                return False