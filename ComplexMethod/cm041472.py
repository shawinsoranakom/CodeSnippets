def test_get_range_object_headers(self, s3_bucket, aws_client):
        object_key = "sample.bin"
        chunk_size = 1024

        with io.BytesIO() as data:
            data.write(os.urandom(chunk_size * 2))
            data.seek(0)
            aws_client.s3.upload_fileobj(data, s3_bucket, object_key)

        range_header = f"bytes=0-{(chunk_size - 1)}"
        resp = aws_client.s3.get_object(Bucket=s3_bucket, Key=object_key, Range=range_header)
        assert resp.get("AcceptRanges") == "bytes"
        resp_headers = resp["ResponseMetadata"]["HTTPHeaders"]
        assert "x-amz-request-id" in resp_headers
        assert "x-amz-id-2" in resp_headers
        # `content-language` should not be in the response
        if is_aws_cloud():  # fixme parity issue
            assert "content-language" not in resp_headers
        # We used to return `cache-control: no-cache` if the header wasn't set
        # by the client, but this was a bug because s3 doesn't do that. It simply
        # omits it.
        assert "cache-control" not in resp_headers
        # Do not send a content-encoding header as discussed in Issue #3608
        assert "content-encoding" not in resp_headers