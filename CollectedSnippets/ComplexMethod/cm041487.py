def test_presigned_url_v4_x_amz_in_qs(
        self,
        s3_bucket,
        s3_create_bucket,
        patch_s3_skip_signature_validation_false,
        create_lambda_function,
        lambda_su_role,
        create_tmp_folder_lambda,
        aws_client,
        snapshot,
    ):
        # test that Boto does not hoist x-amz-storage-class in the query string while pre-signing
        object_key = "temp.txt"
        client = _s3_client_pre_signed_client(
            Config(signature_version="s3v4"),
        )
        url = client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": s3_bucket,
                "Key": object_key,
                "StorageClass": StorageClass.STANDARD,
                "Metadata": {"foo": "bar-complicated-no-random"},
            },
        )
        assert StorageClass.STANDARD not in url
        assert "bar-complicated-no-random" not in url

        handler_file = os.path.join(
            os.path.dirname(__file__), "../lambda_/functions/lambda_s3_integration_presign.mjs"
        )
        temp_folder = create_tmp_folder_lambda(
            handler_file,
            run_command="npm i @aws-sdk/util-endpoints @aws-sdk/client-s3 @aws-sdk/s3-request-presigner @aws-sdk/middleware-endpoint",
        )

        function_name = f"func-integration-{short_uid()}"
        create_lambda_function(
            func_name=function_name,
            zip_file=testutil.create_zip_file(temp_folder, get_content=True),
            runtime=Runtime.nodejs20_x,
            handler="lambda_s3_integration_presign.handler",
            role=lambda_su_role,
            envvars={
                "ACCESS_KEY": s3_constants.DEFAULT_PRE_SIGNED_ACCESS_KEY_ID,
                "SECRET_KEY": s3_constants.DEFAULT_PRE_SIGNED_SECRET_ACCESS_KEY,
            },
        )
        s3_create_bucket(Bucket=function_name)

        response = aws_client.lambda_.invoke(FunctionName=function_name)
        payload = json.load(response["Payload"])
        presigned_url = payload["body"].strip('"')
        # assert that the Javascript SDK hoists it in the URL, unlike Boto
        assert StorageClass.STANDARD in presigned_url
        assert "bar-complicated-no-random" in presigned_url
        # the JS SDK also adds a default checksum now even for pre-signed URLs
        assert "x-amz-checksum-crc32=AAAAAA%3D%3D" in presigned_url

        # missing Content-MD5
        response = requests.put(presigned_url, verify=False, data=b"123456")
        assert response.status_code == 403

        # AWS needs the Content-MD5 header to validate the integrity of the file as set in the pre-signed URL
        # but do not provide StorageClass in the headers, because it's not in SignedHeaders
        response = requests.put(
            presigned_url,
            data=b"123456",
            verify=False,
            headers={"Content-MD5": "4QrcOUm6Wau+VuBX8g+IPg=="},
        )
        assert response.status_code == 200

        # assert that the checksum-crc-32 value is still validated and important for the signature
        bad_presigned_url = presigned_url.replace("crc32=AAAAAA%3D%3D", "crc32=BBBBBB%3D%3D")
        response = requests.put(
            bad_presigned_url,
            data=b"123456",
            verify=False,
            headers={"Content-MD5": "4QrcOUm6Wau+VuBX8g+IPg=="},
        )
        assert response.status_code == 403

        # verify that we properly saved the data
        head_object = aws_client.s3.head_object(
            Bucket=function_name, Key=object_key, ChecksumMode="ENABLED"
        )
        snapshot.match("head-object", head_object)