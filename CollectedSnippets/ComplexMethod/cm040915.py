def complete_multipart(
        self, parts: CompletedPartList, mpu_size: int = None, validation_checksum: str = None
    ):
        last_part_index = len(parts) - 1
        object_etag = hashlib.md5(usedforsecurity=False)
        has_checksum = self.checksum_algorithm is not None
        checksum_hash = None
        checksum_key = None
        if has_checksum:
            checksum_key = f"Checksum{self.checksum_algorithm.upper()}"
            if self.checksum_type == ChecksumType.COMPOSITE:
                checksum_hash = get_s3_checksum(self.checksum_algorithm)
            else:
                checksum_hash = CombinedCrcHash(self.checksum_algorithm)

        pos = 0
        parts_map: dict[str, InternalObjectPart] = {}
        for index, part in enumerate(parts):
            part_number = str(part["PartNumber"])
            part_etag = part["ETag"].strip('"')

            s3_part = self.parts.get(part_number)
            if (
                not s3_part
                or s3_part.etag != part_etag
                or (not has_checksum and any(k.startswith("Checksum") for k in part))
            ):
                raise InvalidPart(
                    "One or more of the specified parts could not be found.  "
                    "The part may not have been uploaded, "
                    "or the specified entity tag may not match the part's entity tag.",
                    ETag=part_etag,
                    PartNumber=part_number,
                    UploadId=self.id,
                )

            if has_checksum:
                if not (part_checksum := part.get(checksum_key)):
                    if self.checksum_type == ChecksumType.COMPOSITE:
                        # weird case, they still try to validate a different checksum type than the multipart
                        for field in part:
                            if field.startswith("Checksum"):
                                algo = field.removeprefix("Checksum").lower()
                                raise BadDigest(
                                    f"The {algo} you specified for part {part_number} did not match what we received."
                                )

                        raise InvalidRequest(
                            f"The upload was created using a {self.checksum_algorithm.lower()} checksum. "
                            f"The complete request must include the checksum for each part. "
                            f"It was missing for part {part_number} in the request."
                        )
                elif part_checksum != s3_part.checksum_value:
                    raise InvalidPart(
                        "One or more of the specified parts could not be found.  The part may not have been uploaded, or the specified entity tag may not match the part's entity tag.",
                        ETag=part_etag,
                        PartNumber=part_number,
                        UploadId=self.id,
                    )

                part_checksum_value = base64.b64decode(s3_part.checksum_value)
                if self.checksum_type == ChecksumType.COMPOSITE:
                    checksum_hash.update(part_checksum_value)
                else:
                    checksum_hash.combine(part_checksum_value, s3_part.size)

            elif any(k.startswith("Checksum") for k in part):
                raise InvalidPart(
                    "One or more of the specified parts could not be found.  The part may not have been uploaded, or the specified entity tag may not match the part's entity tag.",
                    ETag=part_etag,
                    PartNumber=part_number,
                    UploadId=self.id,
                )

            if index != last_part_index and s3_part.size < S3_UPLOAD_PART_MIN_SIZE:
                raise EntityTooSmall(
                    "Your proposed upload is smaller than the minimum allowed size",
                    ETag=part_etag,
                    PartNumber=part_number,
                    MinSizeAllowed=S3_UPLOAD_PART_MIN_SIZE,
                    ProposedSize=s3_part.size,
                )

            object_etag.update(bytes.fromhex(s3_part.etag))
            # keep track of the parts size, as it can be queried afterward on the object as a Range
            internal_part = InternalObjectPart(
                _position=pos,
                Size=s3_part.size,
                ETag=s3_part.etag,
                PartNumber=s3_part.part_number,
            )
            if has_checksum and self.checksum_type == ChecksumType.COMPOSITE:
                internal_part[checksum_key] = s3_part.checksum_value

            parts_map[part_number] = internal_part
            pos += s3_part.size

        if mpu_size and mpu_size != pos:
            raise InvalidRequest(
                f"The provided 'x-amz-mp-object-size' header value {mpu_size} "
                f"does not match what was computed: {pos}"
            )

        if has_checksum:
            checksum_value = base64.b64encode(checksum_hash.digest()).decode()
            if self.checksum_type == ChecksumType.COMPOSITE:
                checksum_value = f"{checksum_value}-{len(parts)}"

            elif self.checksum_type == ChecksumType.FULL_OBJECT:
                if validation_checksum and validation_checksum != checksum_value:
                    raise BadDigest(
                        f"The {self.object.checksum_algorithm.lower()} you specified did not match the calculated checksum."
                    )

            self.checksum_value = checksum_value
            self.object.checksum_value = checksum_value

        multipart_etag = f"{object_etag.hexdigest()}-{len(parts)}"
        self.object.etag = multipart_etag
        self.object.parts = parts_map