def test_s3_get_response_header_overrides(
        self, s3_bucket, signature_version, patch_s3_skip_signature_validation_false, aws_client
    ):
        # Signed requests may include certain header overrides in the querystring
        # https://docs.aws.amazon.com/AmazonS3/latest/API/RESTObjectGET.html
        object_key = "key-header-overrides"
        aws_client.s3.put_object(Bucket=s3_bucket, Key=object_key, Body="something")

        # get object and assert headers
        expiry_date = "Wed, 21 Oct 2015 07:28:00 GMT"
        presigned_client = _s3_client_pre_signed_client(
            Config(signature_version=signature_version), endpoint_url=_endpoint_url()
        )

        url = presigned_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": s3_bucket,
                "Key": object_key,
                "ResponseCacheControl": "max-age=74",
                "ResponseContentDisposition": 'attachment; filename="foo.jpg"',
                "ResponseContentEncoding": "identity",
                "ResponseContentLanguage": "de-DE",
                "ResponseContentType": "image/jpeg",
                "ResponseExpires": expiry_date,
            },
        )
        response = requests.get(url, verify=False)
        assert response.status_code == 200
        headers = response.headers
        assert headers["cache-control"] == "max-age=74"
        assert headers["content-disposition"] == 'attachment; filename="foo.jpg"'
        assert headers["content-encoding"] == "identity"
        assert headers["content-language"] == "de-DE"
        assert headers["content-type"] == "image/jpeg"

        # Note: looks like depending on the environment/libraries, we can get different date formats...
        possible_date_formats = ["2015-10-21T07:28:00Z", expiry_date]
        assert headers["expires"] in possible_date_formats