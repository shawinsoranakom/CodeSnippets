def test_delete_has_empty_content_length_header(self, s3_bucket, aws_client):
        for encoding in None, "gzip":
            # put object
            object_key = "key-by-hostname"
            aws_client.s3.put_object(
                Bucket=s3_bucket,
                Key=object_key,
                Body="something",
                ContentType="text/html; charset=utf-8",
            )
            url = aws_client.s3.generate_presigned_url(
                "delete_object", Params={"Bucket": s3_bucket, "Key": object_key}
            )

            # get object and assert headers
            headers = {}
            if encoding:
                headers["Accept-Encoding"] = encoding
            response = requests.delete(url, headers=headers, verify=False)
            assert not response.content
            assert response.status_code == 204
            assert response.headers.get("x-amz-id-2") is not None
            # AWS does not return a Content-Type when the body is empty and it returns 204
            assert response.headers.get("content-type") is None
            # AWS does not send a content-length header at all
            assert response.headers.get("content-length") is None