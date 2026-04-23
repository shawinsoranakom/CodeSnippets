def test_bucket_does_not_exist(self, s3_vhost_client, snapshot, aws_client):
        snapshot.add_transformer(snapshot.transform.s3_api())
        bucket_name = f"bucket-does-not-exist-{short_uid()}"

        with pytest.raises(ClientError) as e:
            aws_client.s3.list_objects(Bucket=bucket_name)
        e.match("NoSuchBucket")
        snapshot.match("list_object", e.value.response)

        with pytest.raises(ClientError) as e:
            s3_vhost_client.list_objects(Bucket=bucket_name)
        e.match("NoSuchBucket")
        snapshot.match("list_object_vhost", e.value.response)

        bucket_vhost_url = _bucket_url_vhost(bucket_name, region="us-east-1")
        assert "us-east-1" not in bucket_vhost_url

        response = requests.get(bucket_vhost_url)
        assert response.status_code == 404

        bucket_url = _bucket_url(bucket_name, region="us-east-1")
        assert "us-east-1" not in bucket_url
        response = requests.get(bucket_url)
        assert response.status_code == 404

        bucket_vhost_url = _bucket_url_vhost(bucket_name, region="eu-central-1")
        assert "eu-central-1" in bucket_vhost_url
        response = requests.get(bucket_vhost_url)
        assert response.status_code == 404

        bucket_url = _bucket_url(bucket_name, region="eu-central-1")
        assert "eu-central-1" in bucket_url
        response = requests.get(bucket_url)
        assert response.status_code == 404