def upload_part(
        self,
        context: RequestContext,
        request: UploadPartRequest,
    ) -> UploadPartOutput:
        # TODO: missing following parameters:
        #  content_length: ContentLength = None, ->validate?
        #  content_md5: ContentMD5 = None, -> validate?
        #  request_payer: RequestPayer = None,
        bucket_name = request["Bucket"]
        store, s3_bucket = self._get_cross_account_bucket(context, bucket_name)

        upload_id = request.get("UploadId")
        if not (
            s3_multipart := s3_bucket.multiparts.get(upload_id)
        ) or s3_multipart.object.key != request.get("Key"):
            raise NoSuchUpload(
                "The specified upload does not exist. "
                "The upload ID may be invalid, or the upload may have been aborted or completed.",
                UploadId=upload_id,
            )
        elif (part_number := request.get("PartNumber", 0)) < 1 or part_number > 10000:
            raise InvalidArgument(
                "Part number must be an integer between 1 and 10000, inclusive",
                ArgumentName="partNumber",
                ArgumentValue=part_number,
            )

        if content_md5 := request.get("ContentMD5"):
            # assert that the received ContentMD5 is a properly b64 encoded value that fits a MD5 hash length
            if not base_64_content_md5_to_etag(content_md5):
                raise InvalidDigest(
                    "The Content-MD5 you specified was invalid.",
                    Content_MD5=content_md5,
                )

        checksum_algorithm = get_s3_checksum_algorithm_from_request(request)
        checksum_value = (
            request.get(f"Checksum{checksum_algorithm.upper()}") if checksum_algorithm else None
        )

        # TODO: we're not encrypting the object with the provided key for now
        sse_c_key_md5 = request.get("SSECustomerKeyMD5")
        validate_sse_c(
            algorithm=request.get("SSECustomerAlgorithm"),
            encryption_key=request.get("SSECustomerKey"),
            encryption_key_md5=sse_c_key_md5,
        )

        if (s3_multipart.object.sse_key_hash and not sse_c_key_md5) or (
            sse_c_key_md5 and not s3_multipart.object.sse_key_hash
        ):
            raise InvalidRequest(
                "The multipart upload initiate requested encryption. "
                "Subsequent part requests must include the appropriate encryption parameters."
            )
        elif (
            s3_multipart.object.sse_key_hash
            and sse_c_key_md5
            and s3_multipart.object.sse_key_hash != sse_c_key_md5
        ):
            raise InvalidRequest(
                "The provided encryption parameters did not match the ones used originally."
            )

        s3_part = S3Part(
            part_number=part_number,
            checksum_algorithm=checksum_algorithm,
            checksum_value=checksum_value,
        )
        body = request.get("Body")
        headers = context.request.headers
        is_aws_chunked = headers.get("x-amz-content-sha256", "").startswith(
            "STREAMING-"
        ) or "aws-chunked" in headers.get("content-encoding", "")
        # check if chunked request
        if is_aws_chunked:
            checksum_algorithm = (
                checksum_algorithm
                or get_s3_checksum_algorithm_from_trailing_headers(headers.get("x-amz-trailer", ""))
            )
            if checksum_algorithm:
                s3_part.checksum_algorithm = checksum_algorithm

            decoded_content_length = int(headers.get("x-amz-decoded-content-length", 0))
            body = AwsChunkedDecoder(body, decoded_content_length, s3_part)

        if (
            s3_multipart.checksum_algorithm
            and s3_part.checksum_algorithm != s3_multipart.checksum_algorithm
        ):
            error_req_checksum = checksum_algorithm.lower() if checksum_algorithm else "null"
            error_mp_checksum = (
                s3_multipart.object.checksum_algorithm.lower()
                if s3_multipart.object.checksum_algorithm
                else "null"
            )
            if not error_mp_checksum == "null":
                raise InvalidRequest(
                    f"Checksum Type mismatch occurred, expected checksum Type: {error_mp_checksum}, actual checksum Type: {error_req_checksum}"
                )

        stored_multipart = self._storage_backend.get_multipart(bucket_name, s3_multipart)
        with stored_multipart.open(s3_part, mode="w") as stored_s3_part:
            try:
                stored_s3_part.write(body)
            except Exception:
                stored_multipart.remove_part(s3_part)
                raise

            if checksum_algorithm:
                if not validate_checksum_value(s3_part.checksum_value, checksum_algorithm):
                    stored_multipart.remove_part(s3_part)
                    raise InvalidRequest(
                        f"Value for x-amz-checksum-{s3_part.checksum_algorithm.lower()} header is invalid."
                    )
                elif s3_part.checksum_value != stored_s3_part.checksum:
                    stored_multipart.remove_part(s3_part)
                    raise BadDigest(
                        f"The {checksum_algorithm.upper()} you specified did not match the calculated checksum."
                    )

            if content_md5:
                calculated_md5 = etag_to_base_64_content_md5(s3_part.etag)
                if calculated_md5 != content_md5:
                    stored_multipart.remove_part(s3_part)
                    raise BadDigest(
                        "The Content-MD5 you specified did not match what we received.",
                        ExpectedDigest=content_md5,
                        CalculatedDigest=calculated_md5,
                    )

            s3_multipart.parts[str(part_number)] = s3_part

        response = UploadPartOutput(
            ETag=s3_part.quoted_etag,
        )

        add_encryption_to_response(response, s3_object=s3_multipart.object)
        if sse_c_key_md5:
            response["SSECustomerAlgorithm"] = "AES256"
            response["SSECustomerKeyMD5"] = sse_c_key_md5

        if s3_part.checksum_algorithm:
            response[f"Checksum{s3_part.checksum_algorithm.upper()}"] = s3_part.checksum_value

        # TODO: RequestCharged: Optional[RequestCharged]
        return response