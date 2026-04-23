def test_s3_presigned_url_expired(
        self,
        s3_bucket,
        signature_version,
        snapshot,
        patch_s3_skip_signature_validation_false,
        aws_client,
        presigned_snapshot_transformers,
    ):
        object_key = "key-expires-in-2"
        aws_client.s3.put_object(Bucket=s3_bucket, Key=object_key, Body="something")

        # get object and assert headers
        presigned_client = _s3_client_pre_signed_client(
            Config(signature_version=signature_version),
            endpoint_url=_endpoint_url(),
        )
        url = presigned_client.generate_presigned_url(
            "get_object", Params={"Bucket": s3_bucket, "Key": object_key}, ExpiresIn=2
        )
        # retrieving it before expiry
        resp = requests.get(url, verify=False)
        assert resp.status_code == 200
        assert to_str(resp.content) == "something"

        time.sleep(3)  # wait for the URL to expire
        resp = requests.get(url, verify=False)
        resp_content = to_str(resp.content)
        assert resp.status_code == 403
        exception = xmltodict.parse(resp.content)
        snapshot.match("expired-exception", exception)

        assert "<Code>AccessDenied</Code>" in resp_content
        assert "<Message>Request has expired</Message>" in resp_content

        url = presigned_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": s3_bucket, "Key": object_key},
            ExpiresIn=120,
        )

        resp = requests.get(url, verify=False)
        assert resp.status_code == 200
        assert to_str(resp.content) == "something"