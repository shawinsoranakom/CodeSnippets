def test_presigned_post_with_different_user_credentials(
        self,
        aws_client,
        s3_create_bucket_with_client,
        create_role_with_policy,
        account_id,
        wait_and_assume_role,
        snapshot,
    ):
        snapshot.add_transformers_list(
            [
                snapshot.transform.key_value(
                    "HostId", reference_replacement=False, value_replacement="<host-id>"
                ),
                snapshot.transform.key_value("RequestId"),
            ]
        )
        bucket_name = f"bucket-{short_uid()}"
        actions = [
            "s3:CreateBucket",
            "s3:PutObject",
            "s3:GetObject",
            "s3:DeleteBucket",
            "s3:DeleteObject",
        ]

        assume_policy_doc = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {"AWS": account_id},
                    "Effect": "Allow",
                }
            ],
        }
        assume_policy_doc = json.dumps(assume_policy_doc)
        role_name, role_arn = create_role_with_policy(
            effect="Allow",
            actions=actions,
            assume_policy_doc=assume_policy_doc,
            resource="*",
        )

        credentials = wait_and_assume_role(role_arn=role_arn)

        client = boto3.client(
            "s3",
            config=Config(signature_version="s3v4"),
            endpoint_url=_endpoint_url(),
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
        )

        retry(
            lambda: s3_create_bucket_with_client(s3_client=client, Bucket=bucket_name),
            sleep=3 if is_aws_cloud() else 0.5,
        )

        object_key = "validate-policy-full-credentials"
        presigned_request = client.generate_presigned_post(
            Bucket=bucket_name,
            Key=object_key,
            ExpiresIn=60,
            Conditions=[
                {"bucket": bucket_name},
            ],
        )
        # load the generated policy to assert that it kept the casing, and it is sent to AWS
        generated_policy = json.loads(
            base64.b64decode(presigned_request["fields"]["policy"]).decode("utf-8")
        )
        policy_conditions_fields = set()
        token_condition = None
        for condition in generated_policy["conditions"]:
            if isinstance(condition, dict):
                for k, v in condition.items():
                    policy_conditions_fields.add(k)
                    if k == "x-amz-security-token":
                        token_condition = v
            else:
                # format is [operator, key, value]
                policy_conditions_fields.add(condition[1])

        assert policy_conditions_fields == {
            "bucket",
            "key",
            "x-amz-security-token",
            "x-amz-credential",
            "x-amz-date",
            "x-amz-algorithm",
        }
        assert token_condition == credentials["SessionToken"]

        response = requests.post(
            presigned_request["url"],
            data=presigned_request["fields"],
            files={"file": self.DEFAULT_FILE_VALUE},
            verify=False,
        )
        assert response.status_code == 204
        assert response.headers.get("Content-Type") is None

        get_obj = aws_client.s3.get_object(Bucket=bucket_name, Key=object_key)
        snapshot.match("get-obj", get_obj)