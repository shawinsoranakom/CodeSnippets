def test_cors_http_get_no_config(self, s3_bucket, snapshot, aws_client):
        snapshot.add_transformer(
            [
                snapshot.transform.key_value("HostId", reference_replacement=False),
                snapshot.transform.key_value("RequestId"),
            ]
        )
        key = "test-cors-get-no-config"
        body = "cors-test"
        response = aws_client.s3.put_object(Bucket=s3_bucket, Key=key, Body=body, ACL="public-read")
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

        key_url = f"{_bucket_url_vhost(bucket_name=s3_bucket)}/{key}"

        response = requests.get(key_url)
        assert response.status_code == 200
        assert response.text == body
        assert not any("access-control" in header.lower() for header in response.headers)

        response = requests.get(key_url, headers={"Origin": "whatever"})
        assert response.status_code == 200
        assert response.text == body
        assert not any("access-control" in header.lower() for header in response.headers)