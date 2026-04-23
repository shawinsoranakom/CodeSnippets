def test_post_object_policy_conditions_validation_eq(self, s3_bucket, aws_client, snapshot):
        snapshot.add_transformers_list(
            [
                snapshot.transform.key_value(
                    "HostId", reference_replacement=False, value_replacement="<host-id>"
                ),
                snapshot.transform.key_value("RequestId"),
                snapshot.transform.key_value(
                    "ExpiresString", reference_replacement=False, value_replacement="<expires>"
                ),
            ]
        )
        object_key = "validate-policy-1"

        redirect_location = "http://localhost.test/random"
        presigned_request = aws_client.s3.generate_presigned_post(
            Bucket=s3_bucket,
            Key=object_key,
            Fields={"success_action_redirect": redirect_location},
            Conditions=[
                ["eq", "$success_action_redirect", redirect_location],
            ],
            ExpiresIn=60,
        )

        # PostObject with a wrong redirect location
        presigned_request["fields"]["success_action_redirect"] = "http://wrong.location/test"
        response = self.post_generated_presigned_post_with_default_file(presigned_request)

        # assert that it's rejected
        assert response.status_code == 403
        snapshot.match("invalid-condition-eq", xmltodict.parse(response.content))

        # PostObject with a wrong condition (missing $ prefix)
        presigned_request = aws_client.s3.generate_presigned_post(
            Bucket=s3_bucket,
            Key=object_key,
            Fields={"success_action_redirect": redirect_location},
            Conditions=[
                ["eq", "success_action_redirect", redirect_location],
            ],
            ExpiresIn=60,
        )

        response = self.post_generated_presigned_post_with_default_file(presigned_request)

        # assert that it's rejected
        assert response.status_code == 403
        snapshot.match("invalid-condition-missing-prefix", xmltodict.parse(response.content))

        # PostObject with a wrong condition (multiple condition in one dict)
        presigned_request = aws_client.s3.generate_presigned_post(
            Bucket=s3_bucket,
            Key=object_key,
            Fields={"success_action_redirect": redirect_location},
            Conditions=[
                {"bucket": s3_bucket, "success_action_redirect": redirect_location},
            ],
            ExpiresIn=60,
        )

        response = self.post_generated_presigned_post_with_default_file(presigned_request)

        # assert that it's rejected
        assert response.status_code == 400
        snapshot.match("invalid-condition-wrong-condition", xmltodict.parse(response.content))

        # PostObject with a wrong condition value casing
        presigned_request = aws_client.s3.generate_presigned_post(
            Bucket=s3_bucket,
            Key=object_key,
            Fields={"success_action_redirect": redirect_location},
            Conditions=[
                ["eq", "$success_action_redirect", redirect_location.replace("http://", "HTTP://")],
            ],
            ExpiresIn=60,
        )
        response = self.post_generated_presigned_post_with_default_file(presigned_request)
        # assert that it's rejected
        assert response.status_code == 403
        snapshot.match("invalid-condition-wrong-value-casing", xmltodict.parse(response.content))

        object_expires = rfc_1123_datetime(
            datetime.datetime.now(ZoneInfo("GMT")) + datetime.timedelta(minutes=10)
        )

        # test casing for x-amz-meta and specific Content-Type/Expires S3 headers
        presigned_request = aws_client.s3.generate_presigned_post(
            Bucket=s3_bucket,
            Key=object_key,
            ExpiresIn=60,
            Fields={
                "x-amz-meta-test-1": "test-meta-1",
                "x-amz-meta-TEST-2": "test-meta-2",
                "Content-Type": "text/plain",
                "Expires": object_expires,
            },
            Conditions=[
                {"bucket": s3_bucket},
                ["eq", "$x-amz-meta-test-1", "test-meta-1"],
                ["eq", "$x-amz-meta-test-2", "test-meta-2"],
                ["eq", "$content-type", "text/plain"],
                ["eq", "$Expires", object_expires],
            ],
        )
        # assert that it kept the casing
        assert "x-amz-meta-TEST-2" in presigned_request["fields"]
        response = self.post_generated_presigned_post_with_default_file(presigned_request)
        # assert that it's accepted
        assert response.status_code == 204

        head_object = aws_client.s3.head_object(Bucket=s3_bucket, Key=object_key)
        snapshot.match("head-object-metadata", head_object)

        # PostObject with a wrong condition key casing, should still work
        presigned_request = aws_client.s3.generate_presigned_post(
            Bucket=s3_bucket,
            Key=object_key,
            Fields={"success_action_redirect": redirect_location},
            Conditions=[
                ["eq", "$success_Action_REDIRECT", redirect_location],
            ],
            ExpiresIn=60,
        )

        # load the generated policy to assert that it kept the casing, and it is sent to AWS
        generated_policy = json.loads(
            base64.b64decode(presigned_request["fields"]["policy"]).decode("utf-8")
        )
        eq_condition = [
            cond
            for cond in generated_policy["conditions"]
            if isinstance(cond, list) and cond[0] == "eq"
        ][0]
        assert eq_condition[1] == "$success_Action_REDIRECT"

        response = self.post_generated_presigned_post_with_default_file(presigned_request)
        # assert that it's accepted
        assert response.status_code == 303

        final_object = aws_client.s3.get_object(Bucket=s3_bucket, Key=object_key)
        snapshot.match("final-object", final_object)

        # test casing for x-amz-meta and specific Content-Type/Expires S3 headers, but without eq
        presigned_request = aws_client.s3.generate_presigned_post(
            Bucket=s3_bucket,
            Key=object_key,
            ExpiresIn=60,
            Fields={
                "x-amz-meta-test-1": "test-meta-1",
                "x-amz-meta-TEST-2": "test-meta-2",
                "Content-Type": "text/plain",
                "Expires": object_expires,
            },
            Conditions=[
                {"bucket": s3_bucket},
                {"x-amz-meta-test-1": "test-meta-1"},
                {"x-amz-meta-test-2": "test-meta-2"},
                {"Content-Type": "text/plain"},
                {"Expires": object_expires},
            ],
        )
        # assert that it kept the casing
        assert "x-amz-meta-TEST-2" in presigned_request["fields"]
        assert "Content-Type" in presigned_request["fields"]
        response = self.post_generated_presigned_post_with_default_file(presigned_request)
        # assert that it's accepted
        assert response.status_code == 204