def perform_multipart_upload(
        bucket, key, data=None, zipped=False, acl=None, parts: int = 1, **kwargs
    ):
        # beware, the last part can be under 5 MiB, but previous parts needs to be between 5MiB and 5GiB
        if acl:
            kwargs["ACL"] = acl
        multipart_upload_dict = aws_client.s3.create_multipart_upload(
            Bucket=bucket, Key=key, **kwargs
        )
        upload_id = multipart_upload_dict["UploadId"]
        data = data or (5 * short_uid())
        multipart_upload_parts = []
        for part in range(parts):
            # Write contents to memory rather than a file.
            part_number = part + 1

            part_data = data or (5 * short_uid())
            if part_number < parts and ((len_data := len(part_data)) < 5_242_880):
                # data must be at least 5MiB
                multiple = 5_242_880 // len_data
                part_data = part_data * (multiple + 1)

            part_data = to_bytes(part_data)
            upload_file_object = BytesIO(part_data)
            if zipped:
                upload_file_object = BytesIO()
                with gzip.GzipFile(fileobj=upload_file_object, mode="w") as filestream:
                    filestream.write(part_data)

            response = aws_client.s3.upload_part(
                Bucket=bucket,
                Key=key,
                Body=upload_file_object,
                PartNumber=part_number,
                UploadId=upload_id,
            )

            multipart_upload_parts.append({"ETag": response["ETag"], "PartNumber": part_number})
            # multiple parts won't work with zip, stop at one
            if zipped:
                break

        return aws_client.s3.complete_multipart_upload(
            Bucket=bucket,
            Key=key,
            MultipartUpload={"Parts": multipart_upload_parts},
            UploadId=upload_id,
        )