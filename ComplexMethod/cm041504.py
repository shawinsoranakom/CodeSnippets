def test_cross_account_access(self, aws_client, secondary_aws_client, cleanups):
        # GetSecretValue and PutSecretValue can't be used if the default keys are used
        principal_arn = secondary_aws_client.sts.get_caller_identity()["Arn"]
        resource_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": principal_arn},
                    "Action": ["secretsmanager:*"],
                    "Resource": "*",
                }
            ],
        }

        secret_name = f"test-secret-{short_uid()}"
        secret_arn = aws_client.secretsmanager.create_secret(
            Name=secret_name,
            SecretString="secret",
        )["ARN"]

        cleanups.append(
            lambda: aws_client.secretsmanager.delete_secret(
                SecretId=secret_name, ForceDeleteWithoutRecovery=True
            )
        )

        aws_client.secretsmanager.put_resource_policy(
            SecretId=secret_arn, ResourcePolicy=json.dumps(resource_policy)
        )

        # try to access the secret from the secondary account without the resource policy
        response = secondary_aws_client.secretsmanager.describe_secret(SecretId=secret_arn)
        assert response["ARN"] == secret_arn

        kms_default_key_error = (
            "You can't access a secret from a different AWS account if you encrypt the secret "
            "with the default KMS service key."
        )

        with pytest.raises(Exception) as ex:
            secondary_aws_client.secretsmanager.get_secret_value(SecretId=secret_arn)
        assert ex.value.response["Error"]["Code"] == "InvalidRequestException"
        assert ex.value.response["Error"]["Message"] == kms_default_key_error

        with pytest.raises(Exception) as ex:
            secondary_aws_client.secretsmanager.put_secret_value(
                SecretId=secret_arn, SecretString="new-secret"
            )
        assert ex.value.response["Error"]["Code"] == "InvalidRequestException"
        assert ex.value.response["Error"]["Message"] == kms_default_key_error

        # try to add resource policy from the secondary account
        policy = resource_policy
        policy["Statement"][0]["Sid"] = "AllowCrossAccount"
        secondary_aws_client.secretsmanager.put_resource_policy(
            SecretId=secret_arn, ResourcePolicy=json.dumps(policy)
        )

        # try to get the resource policy from the secondary account
        response = secondary_aws_client.secretsmanager.get_resource_policy(SecretId=secret_arn)
        assert json.loads(response["ResourcePolicy"])["Statement"][0]["Sid"] == "AllowCrossAccount"

        # try to access the secret version ids from the secondary account
        response = secondary_aws_client.secretsmanager.list_secret_version_ids(SecretId=secret_arn)
        assert len(response["Versions"]) == 1

        # should not list the secret from the primary account
        response = secondary_aws_client.secretsmanager.list_secrets()
        assert len(response["SecretList"]) == 0

        # set tags from the secondary account
        secondary_aws_client.secretsmanager.tag_resource(
            SecretId=secret_arn, Tags=[{"Key": "tag1", "Value": "value1"}]
        )

        # get tags from the primary account
        response = aws_client.secretsmanager.describe_secret(SecretId=secret_arn)
        assert response["Tags"] == [{"Key": "tag1", "Value": "value1"}]

        # set tags from the secondary account
        secondary_aws_client.secretsmanager.untag_resource(SecretId=secret_arn, TagKeys=["tag1"])

        # get tags from the primary account
        # Note: when removing tags, the response will be empty list in case of AWS,
        # but it will be None in Localstack. To avoid failing the test, we will use the default value as list
        assert poll_condition(
            lambda: (
                aws_client.secretsmanager.describe_secret(SecretId=secret_arn).get("Tags", []) == []
            ),
            timeout=5.0,
            interval=0.5,
        )

        secondary_aws_client.secretsmanager.delete_secret(
            SecretId=secret_arn, ForceDeleteWithoutRecovery=True
        )