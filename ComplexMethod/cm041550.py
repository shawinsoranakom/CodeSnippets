def test_attach_detach_role_policy(self, aws_client, region_name):
        role_name = f"s3-role-{short_uid()}"
        policy_name = f"s3-role-policy-{short_uid()}"

        policy_arns = [p["Arn"] for p in ADDITIONAL_MANAGED_POLICIES.values()]
        policy_arns = [
            arn.replace("arn:aws:", f"arn:{get_partition(region_name)}:") for arn in policy_arns
        ]

        assume_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {"Service": "s3.amazonaws.com"},
                    "Effect": "Allow",
                }
            ],
        }

        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": [
                        "s3:GetReplicationConfiguration",
                        "s3:GetObjectVersion",
                        "s3:ListBucket",
                    ],
                    "Effect": "Allow",
                    "Resource": [f"arn:{get_partition(region_name)}:s3:::bucket_name"],
                }
            ],
        }

        aws_client.iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(assume_policy_document),
        )

        policy_arn = aws_client.iam.create_policy(
            PolicyName=policy_name, Path="/", PolicyDocument=json.dumps(policy_document)
        )["Policy"]["Arn"]
        policy_arns.append(policy_arn)

        # Attach some polices
        for policy_arn in policy_arns:
            rs = aws_client.iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
            assert rs["ResponseMetadata"]["HTTPStatusCode"] == 200

        try:
            # Try to delete role
            aws_client.iam.delete_role(RoleName=role_name)
            pytest.fail("This call should not be successful as the role has policies attached")

        except ClientError as e:
            assert e.response["Error"]["Code"] == "DeleteConflict"

        for policy_arn in policy_arns:
            rs = aws_client.iam.detach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
            assert rs["ResponseMetadata"]["HTTPStatusCode"] == 200

        # clean up
        rs = aws_client.iam.delete_role(RoleName=role_name)
        assert rs["ResponseMetadata"]["HTTPStatusCode"] == 200

        aws_client.iam.delete_policy(PolicyArn=policy_arn)