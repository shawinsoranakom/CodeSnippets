def test_response_structure_get_obj_attrs(self, aws_http_client_factory, s3_bucket, aws_client):
        """
        Test that the response structure is correct for the S3 API for GetObjectAttributes
        The order is important for the Java SDK
        """
        key_name = "get-obj-attrs"
        aws_client.s3.put_object(Bucket=s3_bucket, Key=key_name, Body="test")
        headers = {"x-amz-content-sha256": "UNSIGNED-PAYLOAD"}

        s3_http_client = aws_http_client_factory("s3", signer_factory=SigV4Auth)
        bucket_url = _bucket_url(s3_bucket)

        possible_attrs = ["StorageClass", "ETag", "ObjectSize", "ObjectParts", "Checksum"]

        # GetObjectAttributes
        get_object_attributes_url = f"{bucket_url}/{key_name}?attributes"
        headers["x-amz-object-attributes"] = ",".join(possible_attrs)
        resp = s3_http_client.get(get_object_attributes_url, headers=headers)

        # shuffle the original list
        shuffled_attrs = possible_attrs.copy()
        while shuffled_attrs == possible_attrs:
            random.shuffle(shuffled_attrs)

        assert shuffled_attrs != possible_attrs

        # check that the order of Attributes in the request should not affect the order in the response
        headers["x-amz-object-attributes"] = ",".join(shuffled_attrs)
        resp_randomized = s3_http_client.get(get_object_attributes_url, headers=headers)
        assert resp_randomized.content == resp.content

        def get_ordered_keys(content: bytes) -> list[str]:
            resp_dict = xmltodict.parse(content)
            get_attrs_response = resp_dict["GetObjectAttributesResponse"]
            get_attrs_response.pop("@xmlns", None)
            return list(get_attrs_response.keys())

        ordered_keys = get_ordered_keys(resp.content)
        assert ordered_keys[0] == "ETag"
        assert ordered_keys[1] == "Checksum"
        assert ordered_keys[2] == "StorageClass"
        assert ordered_keys[3] == "ObjectSize"

        # create a Multipart Upload to validate the `ObjectParts` field order
        multipart_key = "multipart-key"
        create_multipart = aws_client.s3.create_multipart_upload(
            Bucket=s3_bucket, Key=multipart_key
        )
        upload_id = create_multipart["UploadId"]
        upload_part = aws_client.s3.upload_part(
            Bucket=s3_bucket,
            Key=multipart_key,
            Body="test",
            PartNumber=1,
            UploadId=upload_id,
        )
        aws_client.s3.complete_multipart_upload(
            Bucket=s3_bucket,
            Key=multipart_key,
            MultipartUpload={"Parts": [{"ETag": upload_part["ETag"], "PartNumber": 1}]},
            UploadId=upload_id,
        )

        get_object_attributes_url = f"{bucket_url}/{multipart_key}?attributes"
        headers["x-amz-object-attributes"] = ",".join(possible_attrs)
        resp = s3_http_client.get(get_object_attributes_url, headers=headers)
        mpu_ordered_keys = get_ordered_keys(resp.content)
        assert mpu_ordered_keys[0] == "ETag"
        assert mpu_ordered_keys[1] == "Checksum"
        assert mpu_ordered_keys[2] == "ObjectParts"
        assert mpu_ordered_keys[3] == "StorageClass"
        assert mpu_ordered_keys[4] == "ObjectSize"