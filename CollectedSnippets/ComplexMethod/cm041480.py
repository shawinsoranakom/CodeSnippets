def test_put_url_metadata_with_sig_s3v4(
        self,
        s3_bucket,
        snapshot,
        aws_client,
        verify_signature,
        monkeypatch,
        presigned_snapshot_transformers,
    ):
        snapshot.add_transformer(snapshot.transform.s3_api())
        snapshot.add_transformer(snapshot.transform.key_value("HostId"))
        snapshot.add_transformer(snapshot.transform.key_value("RequestId"))
        if verify_signature:
            monkeypatch.setattr(config, "S3_SKIP_SIGNATURE_VALIDATION", False)
        else:
            monkeypatch.setattr(config, "S3_SKIP_SIGNATURE_VALIDATION", True)

        presigned_client = _s3_client_pre_signed_client(
            Config(signature_version="s3v4"),
            endpoint_url=_endpoint_url(),
        )

        # Object metadata should be passed as signed headers when sending the pre-signed URL, the boto signer does not
        # append it to the URL
        # https://github.com/localstack/localstack/issues/544
        metadata = {"foo": "bar"}
        object_key = "key-by-hostname"

        # put object via presigned URL with metadata
        url = presigned_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": s3_bucket, "Key": object_key, "Metadata": metadata},
        )
        assert "x-amz-meta-foo=bar" not in url

        # put the request without the headers
        response = requests.put(url, data="content 123")
        # if we skip validation, it should work for LocalStack
        if not verify_signature and not is_aws_cloud():
            assert response.ok, f"response returned {response.status_code}: {response.text}"
            # response body should be empty, see https://github.com/localstack/localstack/issues/1317
            assert not response.text
        else:
            assert response.status_code == 403
            exception = xmltodict.parse(response.content)
            snapshot.match("no-meta-headers", exception)

        # put it now with the signed headers
        response = requests.put(url, data="content 123", headers={"x-amz-meta-foo": "bar"})
        # assert metadata is present
        assert response.ok

        response = aws_client.s3.head_object(Bucket=s3_bucket, Key=object_key)
        assert response["Metadata"]["foo"] == "bar"
        snapshot.match("head_object", response)

        # assert with another metadata, should fail if verify_signature is not True
        response = requests.put(url, data="content 123", headers={"x-amz-meta-wrong": "wrong"})

        # if we skip validation, it should work for LocalStack
        if not verify_signature and not is_aws_cloud():
            assert response.ok, f"response returned {response.status_code}: {response.text}"
        else:
            assert response.status_code == 403
            exception = xmltodict.parse(response.content)
            snapshot.match("wrong-meta-headers", exception)

        head_object = aws_client.s3.head_object(Bucket=s3_bucket, Key=object_key)
        if not verify_signature and not is_aws_cloud():
            assert head_object["Metadata"]["wrong"] == "wrong"
        else:
            assert "wrong" not in head_object["Metadata"]