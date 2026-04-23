def get_object(
        self,
        key: ObjectKey,
        version_id: ObjectVersionId = None,
        http_method: Literal["GET", "PUT", "HEAD", "DELETE"] = "GET",
    ) -> "S3Object":
        """
        :param key: the Object Key
        :param version_id: optional, the versionId of the object
        :param http_method: the HTTP method of the original call. This is necessary for the exception if the bucket is
        versioned or suspended
        see: https://docs.aws.amazon.com/AmazonS3/latest/userguide/DeleteMarker.html
        :return: the S3Object from the bucket
        :raises NoSuchKey if the object key does not exist at all, or if the object is a DeleteMarker
        :raises MethodNotAllowed if the object is a DeleteMarker and the operation is not allowed against it
        """

        if self.versioning_status is None:
            if version_id and version_id != "null":
                raise InvalidArgument(
                    "Invalid version id specified",
                    ArgumentName="versionId",
                    ArgumentValue=version_id,
                )

            s3_object = self.objects.get(key)

            if not s3_object:
                raise NoSuchKey("The specified key does not exist.", Key=key)

        else:
            self.objects: VersionedKeyStore
            if version_id:
                s3_object_version = self.objects.get(key, version_id)
                if not s3_object_version:
                    raise NoSuchVersion(
                        "The specified version does not exist.",
                        Key=key,
                        VersionId=version_id,
                    )
                elif isinstance(s3_object_version, S3DeleteMarker):
                    if http_method == "HEAD":
                        raise CommonServiceException(
                            code="405",
                            message="Method Not Allowed",
                            status_code=405,
                        )

                    raise MethodNotAllowed(
                        "The specified method is not allowed against this resource.",
                        Method=http_method,
                        ResourceType="DeleteMarker",
                        DeleteMarker=True,
                        Allow="DELETE",
                        VersionId=s3_object_version.version_id,
                    )
                return s3_object_version

            s3_object = self.objects.get(key)

            if not s3_object:
                raise NoSuchKey("The specified key does not exist.", Key=key)

            elif isinstance(s3_object, S3DeleteMarker):
                if http_method not in ("HEAD", "GET"):
                    raise MethodNotAllowed(
                        "The specified method is not allowed against this resource.",
                        Method=http_method,
                        ResourceType="DeleteMarker",
                        DeleteMarker=True,
                        Allow="DELETE",
                        VersionId=s3_object.version_id,
                    )

                raise NoSuchKey(
                    "The specified key does not exist.",
                    Key=key,
                    DeleteMarker=True,
                    VersionId=s3_object.version_id,
                )

        return s3_object