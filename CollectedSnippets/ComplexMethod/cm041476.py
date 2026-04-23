def test_response_structure(self, aws_http_client_factory, s3_bucket, aws_client):
        """
        Test that the response structure is correct for the S3 API
        """
        aws_client.s3.put_object(Bucket=s3_bucket, Key="test", Body="test")
        headers = {"x-amz-content-sha256": "UNSIGNED-PAYLOAD"}

        s3_http_client = aws_http_client_factory("s3", signer_factory=SigV4Auth)

        # Lists all buckets
        endpoint_url = _endpoint_url()
        resp = s3_http_client.get(endpoint_url, headers=headers)
        assert b'<?xml version="1.0" encoding="UTF-8"?>\n' in get_xml_content(resp.content)

        resp_dict = xmltodict.parse(resp.content)
        assert "ListAllMyBucketsResult" in resp_dict
        # validate that the Owner tag is first, before Buckets. This is because the Java SDK is counting on the order
        # to properly set the Owner value to the buckets.
        assert (
            resp_dict["ListAllMyBucketsResult"].pop("@xmlns")
            == "http://s3.amazonaws.com/doc/2006-03-01/"
        )
        list_buckets_tags = list(resp_dict["ListAllMyBucketsResult"].keys())
        assert list_buckets_tags[0] == "Owner"
        assert list_buckets_tags[1] == "Buckets"

        # Lists all objects in a bucket
        bucket_url = _bucket_url(s3_bucket)
        resp = s3_http_client.get(bucket_url, headers=headers)
        assert b'<?xml version="1.0" encoding="UTF-8"?>\n' in get_xml_content(resp.content)
        resp_dict = xmltodict.parse(resp.content)
        assert "ListBucketResult" in resp_dict
        assert resp_dict["ListBucketResult"]["@xmlns"] == "http://s3.amazonaws.com/doc/2006-03-01/"
        # validate that the Contents tag is last, after BucketName. Again for the Java SDK to properly set the
        # BucketName value to the objects.
        list_objects_tags = list(resp_dict["ListBucketResult"].keys())
        assert list_objects_tags.index("Name") < list_objects_tags.index("Contents")
        assert list_objects_tags[-1] == "Contents"

        # Lists all objects V2 in a bucket
        list_objects_v2_url = f"{bucket_url}?list-type=2"
        resp = s3_http_client.get(list_objects_v2_url, headers=headers)
        assert b'<?xml version="1.0" encoding="UTF-8"?>\n' in get_xml_content(resp.content)
        resp_dict = xmltodict.parse(resp.content)
        assert "ListBucketResult" in resp_dict
        assert resp_dict["ListBucketResult"]["@xmlns"] == "http://s3.amazonaws.com/doc/2006-03-01/"
        # same as ListObjects
        list_objects_v2_tags = list(resp_dict["ListBucketResult"].keys())
        assert list_objects_v2_tags.index("Name") < list_objects_v2_tags.index("Contents")
        assert list_objects_v2_tags[-1] == "Contents"

        # Lists all multipart uploads in a bucket
        list_multipart_uploads_url = f"{bucket_url}?uploads"
        resp = s3_http_client.get(list_multipart_uploads_url, headers=headers)
        assert b'<?xml version="1.0" encoding="UTF-8"?>\n' in get_xml_content(resp.content)
        resp_dict = xmltodict.parse(resp.content)
        assert "ListMultipartUploadsResult" in resp_dict
        assert (
            resp_dict["ListMultipartUploadsResult"]["@xmlns"]
            == "http://s3.amazonaws.com/doc/2006-03-01/"
        )

        # GetBucketLocation
        location_constraint_url = f"{bucket_url}?location"
        resp = s3_http_client.get(location_constraint_url, headers=headers)
        xml_content = get_xml_content(resp.content)
        assert b'<?xml version="1.0" encoding="UTF-8"?>\n' in xml_content
        assert b'<LocationConstraint xmlns="http://s3.amazonaws.com/doc/2006-03-01/"' in xml_content

        tagging = {"TagSet": [{"Key": "tag1", "Value": "tag1"}]}
        # put some tags on the bucket
        aws_client.s3.put_bucket_tagging(Bucket=s3_bucket, Tagging=tagging)

        # GetBucketTagging
        get_bucket_tagging_url = f"{bucket_url}?tagging"
        resp = s3_http_client.get(get_bucket_tagging_url, headers=headers)
        resp_dict = xmltodict.parse(resp.content)
        assert resp_dict["Tagging"]["TagSet"] == {"Tag": {"Key": "tag1", "Value": "tag1"}}
        assert resp_dict["Tagging"]["@xmlns"] == "http://s3.amazonaws.com/doc/2006-03-01/"

        # put an object to tests the next requests
        key_name = "test-key"
        aws_client.s3.put_object(Bucket=s3_bucket, Key=key_name, Tagging="tag1=tag1")

        # Lists all objects versions in a bucket
        list_objects_version_url = f"{bucket_url}?versions"
        resp = s3_http_client.get(list_objects_version_url, headers=headers)
        assert b'<?xml version="1.0" encoding="UTF-8"?>\n' in get_xml_content(resp.content)
        resp_dict = xmltodict.parse(resp.content)
        assert "ListVersionsResult" in resp_dict
        assert (
            resp_dict["ListVersionsResult"]["@xmlns"] == "http://s3.amazonaws.com/doc/2006-03-01/"
        )
        # same as ListObjects
        list_objects_versions_tags = list(resp_dict["ListVersionsResult"].keys())
        assert list_objects_versions_tags.index("Name") < list_objects_versions_tags.index(
            "Version"
        )
        assert list_objects_versions_tags[-1] == "Version"

        # GetObjectTagging
        get_object_tagging_url = f"{bucket_url}/{key_name}?tagging"
        resp = s3_http_client.get(get_object_tagging_url, headers=headers)
        resp_dict = xmltodict.parse(resp.content)
        assert resp_dict["Tagging"]["TagSet"] == {"Tag": {"Key": "tag1", "Value": "tag1"}}
        assert resp_dict["Tagging"]["@xmlns"] == "http://s3.amazonaws.com/doc/2006-03-01/"

        # CopyObject
        get_object_tagging_url = f"{bucket_url}/{key_name}?tagging"
        resp = s3_http_client.get(get_object_tagging_url, headers=headers)
        resp_dict = xmltodict.parse(resp.content)
        assert resp_dict["Tagging"]["TagSet"] == {"Tag": {"Key": "tag1", "Value": "tag1"}}
        assert resp_dict["Tagging"]["@xmlns"] == "http://s3.amazonaws.com/doc/2006-03-01/"

        copy_object_url = f"{bucket_url}/copied-key"
        copy_object_headers = {**headers, "x-amz-copy-source": f"{bucket_url}/{key_name}"}
        resp = s3_http_client.put(copy_object_url, headers=copy_object_headers)
        resp_dict = xmltodict.parse(resp.content)
        assert "CopyObjectResult" in resp_dict
        assert resp_dict["CopyObjectResult"]["@xmlns"] == "http://s3.amazonaws.com/doc/2006-03-01/"
        assert resp.status_code == 200

        multipart_key = "multipart-key"
        create_multipart = aws_client.s3.create_multipart_upload(
            Bucket=s3_bucket, Key=multipart_key
        )
        upload_id = create_multipart["UploadId"]

        upload_part_url = f"{bucket_url}/{multipart_key}?UploadId={upload_id}&PartNumber=1"
        resp = s3_http_client.put(upload_part_url, headers=headers)
        assert not resp.content, resp.content
        assert resp.status_code == 200
        assert resp.headers.get("Content-Type") is None
        assert resp.headers["Content-Length"] == "0"

        # DeleteObjectTagging
        resp = s3_http_client.delete(get_object_tagging_url, headers=headers)
        assert not resp.content, resp.content
        assert resp.status_code == 204
        assert resp.headers.get("Content-Type") is None
        assert resp.headers.get("Content-Length") is None