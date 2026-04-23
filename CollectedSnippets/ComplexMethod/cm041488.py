def test_s3_ignored_special_headers(
        self,
        s3_bucket,
        patch_s3_skip_signature_validation_false,
        monkeypatch,
    ):
        # if the crt.auth is not available, not need to patch as it will use it by default
        if find_spec("botocore.crt.auth"):
            # the CRT client does not allow us to pass a protected header, it will trigger an exception, so we need
            # to patch the Signer selection to the Python implementation which does not have this check
            from botocore.auth import AUTH_TYPE_MAPS, S3SigV4QueryAuth

            monkeypatch.setitem(AUTH_TYPE_MAPS, "s3v4-query", S3SigV4QueryAuth)

        key = "my-key"
        presigned_client = _s3_client_pre_signed_client(
            Config(signature_version="s3v4", s3={"payload_signing_enabled": True}),
            endpoint_url=_endpoint_url(),
        )

        def add_content_sha_header(request, **kwargs):
            request.headers["x-amz-content-sha256"] = "UNSIGNED-PAYLOAD"

        presigned_client.meta.events.register(
            "before-sign.s3.PutObject",
            handler=add_content_sha_header,
        )
        try:
            url = presigned_client.generate_presigned_url(
                "put_object", Params={"Bucket": s3_bucket, "Key": key}
            )
            assert "x-amz-content-sha256" in url
            # somehow, it's possible to add "x-amz-content-sha256" to signed headers, the AWS Go SDK does it
            resp = requests.put(
                url,
                data="something",
                verify=False,
                headers={"x-amz-content-sha256": "UNSIGNED-PAYLOAD"},
            )
            assert resp.ok

            # if signed but not provided, AWS will raise an exception
            resp = requests.put(url, data="something", verify=False)
            assert resp.status_code == 403

        finally:
            presigned_client.meta.events.unregister(
                "before-sign.s3.PutObject",
                add_content_sha_header,
            )

        # recreate the request, without the signed header
        url = presigned_client.generate_presigned_url(
            "put_object", Params={"Bucket": s3_bucket, "Key": key}
        )
        assert "x-amz-content-sha256" not in url

        # assert that if provided and not signed, AWS will ignore it even if it starts with `x-amz`
        resp = requests.put(
            url,
            data="something",
            verify=False,
            headers={"x-amz-content-sha256": "UNSIGNED-PAYLOAD"},
        )
        assert resp.ok

        # assert that x-amz-user-agent is not ignored, it must be set in SignedHeaders
        resp = requests.put(
            url, data="something", verify=False, headers={"x-amz-user-agent": "test"}
        )
        assert resp.status_code == 403

        # X-Amz-Signature needs to be the last query string parameter: insert x-id before like the Go SDK
        index = url.find("&X-Amz-Signature")
        rewritten_url = url[:index] + "&x-id=PutObject" + url[index:]
        # however, the x-id query string parameter is not ignored
        resp = requests.put(rewritten_url, data="something", verify=False)
        assert resp.status_code == 403