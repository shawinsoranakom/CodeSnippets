def test_presigned_url_signature_authentication(
        self,
        s3_create_bucket,
        signature_version,
        use_virtual_address,
        snapshot,
        patch_s3_skip_signature_validation_false,
        aws_client,
        presigned_snapshot_transformers,
    ):
        bucket_name = f"presign-{short_uid()}"

        s3_endpoint_path_style = _endpoint_url()
        s3_url = _bucket_url_vhost(bucket_name) if use_virtual_address else _bucket_url(bucket_name)

        s3_create_bucket(Bucket=bucket_name)
        object_key = "temp.txt"
        aws_client.s3.put_object(Key=object_key, Bucket=bucket_name, Body="123")

        s3_config = {"addressing_style": "virtual"} if use_virtual_address else {}
        client = _s3_client_pre_signed_client(
            Config(signature_version=signature_version, s3=s3_config),
            endpoint_url=s3_endpoint_path_style,
        )

        expires = 20

        # GET requests
        simple_params = {"Bucket": bucket_name, "Key": object_key}
        url = _generate_presigned_url(client, simple_params, expires)
        response = requests.get(url)
        assert response.status_code == 200
        assert response.content == b"123"

        params = {
            "Bucket": bucket_name,
            "Key": object_key,
            "ResponseContentType": "text/plain",
            "ResponseContentDisposition": "attachment;  filename=test.txt",
        }

        presigned = _generate_presigned_url(client, params, expires)
        response = requests.get(presigned)
        assert response.status_code == 200
        assert response.content == b"123"

        object_data = f"this should be found in when you download {object_key}."

        # invalid requests
        response = requests.get(
            _make_url_invalid(s3_url, object_key, presigned),
            data=object_data,
            headers={"Content-Type": "my-fake-content/type"},
        )
        assert response.status_code == 403
        exception = xmltodict.parse(response.content)
        snapshot.match("invalid-get-1", exception)

        # put object valid
        response = requests.put(
            _generate_presigned_url(client, simple_params, expires, client_method="put_object"),
            data=object_data,
        )
        # body should be empty, and it will show us the exception if it's not
        assert not response.content
        assert response.status_code == 200

        params = {
            "Bucket": bucket_name,
            "Key": object_key,
            "ContentType": "text/plain",
        }
        presigned_put_url = _generate_presigned_url(
            client, params, expires, client_method="put_object"
        )
        response = requests.put(
            presigned_put_url,
            data=object_data,
            headers={"Content-Type": "text/plain"},
        )
        assert not response.content
        assert response.status_code == 200

        # Invalid request
        response = requests.put(
            _make_url_invalid(s3_url, object_key, presigned_put_url),
            data=object_data,
            headers={"Content-Type": "my-fake-content/type"},
        )
        assert response.status_code == 403
        exception = xmltodict.parse(response.content)
        snapshot.match("invalid-put-1", exception)

        # DELETE requests
        presigned_delete_url = _generate_presigned_url(
            client, simple_params, expires, client_method="delete_object"
        )
        response = requests.delete(presigned_delete_url)
        assert response.status_code == 204