def test_s3_timestamp_precision(self, s3_bucket, aws_client, aws_http_client_factory):
        object_key = "test-key"
        aws_client.s3.put_object(Bucket=s3_bucket, Key=object_key, Body="test-body")

        def assert_timestamp_is_iso8061_s3_format(_timestamp: str):
            # the timestamp should be looking like the following
            # 2023-11-15T12:02:40.000Z
            assert _timestamp.endswith(".000Z")
            assert len(_timestamp) == 24
            # assert that it follows the right format and it does not raise an exception during parsing
            parsed_ts = datetime.datetime.strptime(_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
            assert parsed_ts.microsecond == 0

        s3_http_client = aws_http_client_factory("s3", signer_factory=SigV4Auth)
        list_buckets_endpoint = _endpoint_url()
        list_buckets_resp = s3_http_client.get(
            list_buckets_endpoint, headers={"x-amz-content-sha256": "UNSIGNED-PAYLOAD"}
        )
        list_buckets_dict = xmltodict.parse(list_buckets_resp.content)

        buckets = list_buckets_dict["ListAllMyBucketsResult"]["Buckets"]["Bucket"]
        # because of XML parsing, it can either be a list or a dict

        if isinstance(buckets, list):
            bucket = buckets[0]
        else:
            bucket = buckets
        bucket_timestamp: str = bucket["CreationDate"]
        assert_timestamp_is_iso8061_s3_format(bucket_timestamp)

        bucket_url = _bucket_url(s3_bucket)
        object_url = f"{bucket_url}/{object_key}"
        head_obj_resp = s3_http_client.head(
            object_url, headers={"x-amz-content-sha256": "UNSIGNED-PAYLOAD"}
        )
        last_modified: str = head_obj_resp.headers["Last-Modified"]
        assert datetime.datetime.strptime(last_modified, RFC1123)
        assert last_modified.endswith(" GMT")

        get_obj_resp = s3_http_client.get(
            object_url, headers={"x-amz-content-sha256": "UNSIGNED-PAYLOAD"}
        )
        last_modified: str = get_obj_resp.headers["Last-Modified"]
        assert datetime.datetime.strptime(last_modified, RFC1123)
        assert last_modified.endswith(" GMT")

        object_attrs_url = f"{object_url}?attributes"
        get_obj_attrs_resp = s3_http_client.get(
            object_attrs_url,
            headers={"x-amz-content-sha256": "UNSIGNED-PAYLOAD", "x-amz-object-attributes": "ETag"},
        )
        last_modified: str = get_obj_attrs_resp.headers["Last-Modified"]
        assert datetime.datetime.strptime(last_modified, RFC1123)
        assert last_modified.endswith(" GMT")

        copy_object_url = f"{bucket_url}/copied-key"
        copy_resp = s3_http_client.put(
            copy_object_url,
            headers={
                "x-amz-content-sha256": "UNSIGNED-PAYLOAD",
                "x-amz-copy-source": f"{bucket_url}/{object_key}",
            },
        )
        copy_resp_dict = xmltodict.parse(copy_resp.content)
        copy_timestamp: str = copy_resp_dict["CopyObjectResult"]["LastModified"]
        assert_timestamp_is_iso8061_s3_format(copy_timestamp)