def test_set_external_hostname(
        self, s3_bucket, allow_bucket_acl, s3_multipart_upload, monkeypatch, snapshot, aws_client
    ):
        snapshot.add_transformer(
            [
                snapshot.transform.key_value("Location"),
                snapshot.transform.key_value("Bucket"),
            ]
        )
        custom_hostname = "foobar"
        monkeypatch.setattr(
            config,
            "LOCALSTACK_HOST",
            config.HostAndPort(host=custom_hostname, port=config.GATEWAY_LISTEN[0].port),
        )
        key = "test.file"
        content = "test content 123"
        acl = "public-read"
        # upload file
        response = s3_multipart_upload(bucket=s3_bucket, key=key, data=content, acl=acl)
        snapshot.match("multipart-upload", response)

        assert s3_bucket in response["Location"]
        assert key in response["Location"]
        if not is_aws_cloud():
            expected_url = (
                f"{_bucket_url(bucket_name=s3_bucket, localstack_host=custom_hostname)}/{key}"
            )
            assert response["Location"] == expected_url

        # download object via API
        downloaded_object = aws_client.s3.get_object(Bucket=s3_bucket, Key=key)
        snapshot.match("get-object", response)
        assert content == to_str(downloaded_object["Body"].read())

        # download object directly from download link
        download_url = response["Location"].replace(
            f"{get_localstack_host().host}:", "localhost.localstack.cloud:"
        )
        response = requests.get(download_url)
        assert response.status_code == 200
        assert to_str(response.content) == content