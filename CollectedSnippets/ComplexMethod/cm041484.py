def test_s3_put_presigned_url_with_different_headers(
        self,
        s3_bucket,
        signature_version,
        snapshot,
        patch_s3_skip_signature_validation_false,
        aws_client,
        presigned_snapshot_transformers,
    ):
        object_key = "key-double-header-param"
        aws_client.s3.put_object(Bucket=s3_bucket, Key=object_key, Body="something")

        presigned_client = _s3_client_pre_signed_client(
            Config(signature_version=signature_version),
            endpoint_url=_endpoint_url(),
        )
        # Content-Type, Content-MD5 and Date are specific headers for SigV2 and are checked
        # others are not verified in the signature
        # Manually set the content-type for it to be added to the signature
        presigned_url = presigned_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": s3_bucket,
                "Key": object_key,
                "ContentType": "text/plain",
            },
            ExpiresIn=10,
        )
        # Use the pre-signed URL with the right ContentType
        response = requests.put(
            presigned_url,
            data="test_data",
            headers={"Content-Type": "text/plain"},
        )
        assert not response.content
        assert response.status_code == 200

        # Use the pre-signed URL with the wrong ContentType
        response = requests.put(
            presigned_url,
            data="test_data",
            headers={"Content-Type": "text/xml"},
        )
        assert response.status_code == 403

        exception = xmltodict.parse(response.content)
        exception["StatusCode"] = response.status_code
        snapshot.match("content-type-exception", exception)

        if signature_version == "s3":
            # we sleep 1 second to allow the StringToSign value in the exception change between both call
            # (timestamped value, to avoid the test being flaky)
            time.sleep(1.1)

        # regenerate a new pre-signed URL with no content-type specified
        presigned_url = presigned_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": s3_bucket,
                "Key": object_key,
                "ContentEncoding": "identity",
            },
            ExpiresIn=10,
        )

        # send the pre-signed URL with the right ContentEncoding
        response = requests.put(
            presigned_url,
            data="test_data",
            headers={"Content-Encoding": "identity"},
        )
        assert not response.content
        assert response.status_code == 200

        # send the pre-signed URL with the right ContentEncoding but a new ContentType
        # should fail with SigV2 and succeed with SigV4
        response = requests.put(
            presigned_url,
            data="test_data",
            headers={"Content-Encoding": "identity", "Content-Type": "text/xml"},
        )
        if signature_version == "s3":
            assert response.status_code == 403
        else:
            assert response.status_code == 200

        exception = xmltodict.parse(response.content) if response.content else {}
        exception["StatusCode"] = response.status_code
        snapshot.match("content-type-response", exception)

        # now send the pre-signed URL with the wrong ContentEncoding
        # should succeed with SigV2 as only hard coded headers are checked
        # but fail with SigV4 as Content-Encoding was part of the signed headers
        response = requests.put(
            presigned_url,
            data="test_data",
            headers={"Content-Encoding": "gzip"},
        )
        if signature_version == "s3":
            assert response.status_code == 200
        else:
            assert response.status_code == 403
        exception = xmltodict.parse(response.content) if response.content else {}
        exception["StatusCode"] = response.status_code
        snapshot.match("wrong-content-encoding-response", exception)