def test_s3_presigned_post_success_action_status_201_response(
        self, s3_bucket, aws_client, region_name
    ):
        # a security policy is required if the bucket is not publicly writable
        # see https://docs.aws.amazon.com/AmazonS3/latest/API/RESTObjectPOST.html#RESTObjectPOST-requests-form-fields
        body = "something body"
        # get presigned URL
        object_key = "key-${filename}"
        presigned_request = aws_client.s3.generate_presigned_post(
            Bucket=s3_bucket,
            Key=object_key,
            Fields={"success_action_status": "201"},
            Conditions=[{"bucket": s3_bucket}, ["eq", "$success_action_status", "201"]],
            ExpiresIn=60,
        )
        files = {"file": ("my-file", body)}
        response = requests.post(
            presigned_request["url"],
            data=presigned_request["fields"],
            files=files,
            verify=False,
        )

        assert response.status_code == 201
        json_response = xmltodict.parse(response.content)
        assert "PostResponse" in json_response
        json_response = json_response["PostResponse"]

        etag = '"43281e21fce675ac3bcb3524b38ca4ed"'
        assert response.headers["ETag"] == etag

        location = f"{_bucket_url_vhost(s3_bucket, region_name)}/key-my-file"
        if region_name != "us-east-1":
            # the format is a bit different for non-default regions, we don't return the region as part of the
            # `Location` to avoid SSL issue, but we still want to test it works with `_bucket_url_vhost`
            location = location.replace(f".{region_name}.", ".")

        assert response.headers["Location"] == location
        assert json_response["Location"] == location

        assert json_response["Bucket"] == s3_bucket
        assert json_response["Key"] == "key-my-file"
        assert json_response["ETag"] == etag