def _assert_invocations():
            with ThreadPoolExecutor(2) as executor:
                results = list(executor.map(_invoke_lambda, range(2)))
            assert len(results) == 2
            assert (
                results[0]["AWS_LAMBDA_LOG_STREAM_NAME"] != results[1]["AWS_LAMBDA_LOG_STREAM_NAME"]
            ), "Environments identical for both invocations"
            # if we got different environments, those should differ as well
            assert results[0]["AWS_ACCESS_KEY_ID"] != results[1]["AWS_ACCESS_KEY_ID"], (
                "Access Key IDs have to differ"
            )
            assert results[0]["AWS_SECRET_ACCESS_KEY"] != results[1]["AWS_SECRET_ACCESS_KEY"], (
                "Secret Access keys have to differ"
            )
            assert results[0]["AWS_SESSION_TOKEN"] != results[1]["AWS_SESSION_TOKEN"], (
                "Session tokens have to differ"
            )
            # check if the access keys match the same role, and the role matches the one provided
            # since a lot of asserts are based on the structure of the arns, snapshots are not too nice here, so manual
            keys_1 = _transform_to_key_dict(results[0])
            keys_2 = _transform_to_key_dict(results[1])
            sts_client_1 = create_client_with_keys("sts", keys=keys_1, region_name=region_name)
            sts_client_2 = create_client_with_keys("sts", keys=keys_2, region_name=region_name)
            identity_1 = sts_client_1.get_caller_identity()
            identity_2 = sts_client_2.get_caller_identity()
            assert identity_1["Arn"] == identity_2["Arn"]
            role_part = (
                identity_1["Arn"]
                .replace("sts", "iam")
                .replace("assumed-role", "role")
                .rpartition("/")
            )
            assert lambda_su_role == role_part[0]
            assert function_name == role_part[2]
            assert identity_1["Account"] == identity_2["Account"]
            assert identity_1["UserId"] == identity_2["UserId"]
            assert function_name == identity_1["UserId"].partition(":")[2]