def test_put_object_with_md5_and_chunk_signature_bad_headers(
        self,
        s3_bucket,
        signature_version,
        verify_signature,
        monkeypatch,
        snapshot,
        aws_client,
        presigned_snapshot_transformers,
    ):
        snapshotted = False
        if verify_signature:
            monkeypatch.setattr(config, "S3_SKIP_SIGNATURE_VALIDATION", False)
            snapshotted = True
        else:
            monkeypatch.setattr(config, "S3_SKIP_SIGNATURE_VALIDATION", True)

        object_key = "test-runtime.properties"
        content_md5 = "pX8KKuGXS1f2VTcuJpqjkw=="
        headers = {
            "Content-Md5": content_md5,
            "Content-Type": "application/octet-stream",
            "X-Amz-Content-Sha256": "STREAMING-AWS4-HMAC-SHA256-PAYLOAD",
            "X-Amz-Date": "20211122T191045Z",
            "X-Amz-Decoded-Content-Length": "test",  # string instead of int
            "Content-Length": "10",
            "Connection": "Keep-Alive",
            "Expect": "100-continue",
        }

        presigned_client = _s3_client_pre_signed_client(
            Config(signature_version=signature_version),
            endpoint_url=_endpoint_url(),
        )
        url = presigned_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": s3_bucket,
                "Key": object_key,
                "ContentType": "application/octet-stream",
                "ContentMD5": content_md5,
            },
        )
        result = requests.put(url, data="test", headers=headers)
        assert result.status_code == 403
        if snapshotted:
            exception = xmltodict.parse(result.content)
            snapshot.match("with-decoded-content-length", exception)

        if signature_version == "s3" or (not verify_signature and not is_aws_cloud()):
            assert b"SignatureDoesNotMatch" in result.content
        # we are either using s3v4 with new provider or whichever signature against AWS
        else:
            assert b"AccessDenied" in result.content

        # check also no X-Amz-Decoded-Content-Length
        headers.pop("X-Amz-Decoded-Content-Length")
        result = requests.put(url, data="test", headers=headers)
        assert result.status_code == 403, (result, result.content)
        if snapshotted:
            exception = xmltodict.parse(result.content)
            snapshot.match("without-decoded-content-length", exception)
        if signature_version == "s3" or (not verify_signature and not is_aws_cloud()):
            assert b"SignatureDoesNotMatch" in result.content
        else:
            assert b"AccessDenied" in result.content