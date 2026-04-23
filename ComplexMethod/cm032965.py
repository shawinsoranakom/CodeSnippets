def validate_connector_settings(self) -> None:
        """Validate connector settings"""
        if self.s3_client is None:
            raise ConnectorMissingCredentialError(
                "Blob storage credentials not loaded."
            )

        if not self.bucket_name:
            raise ConnectorValidationError(
                "No bucket name was provided in connector settings."
            )

        try:
            # Lightweight validation step
            self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=self.prefix, MaxKeys=1
            )

        except Exception as e:
            error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', '')
            status_code = getattr(e, 'response', {}).get('ResponseMetadata', {}).get('HTTPStatusCode')

            # Common S3 error scenarios
            if error_code in [
                "AccessDenied",
                "InvalidAccessKeyId",
                "SignatureDoesNotMatch",
            ]:
                if status_code == 403 or error_code == "AccessDenied":
                    raise InsufficientPermissionsError(
                        f"Insufficient permissions to list objects in bucket '{self.bucket_name}'. "
                        "Please check your bucket policy and/or IAM policy."
                    )
                if status_code == 401 or error_code == "SignatureDoesNotMatch":
                    raise CredentialExpiredError(
                        "Provided blob storage credentials appear invalid or expired."
                    )

                raise CredentialExpiredError(
                    f"Credential issue encountered ({error_code})."
                )

            if error_code == "NoSuchBucket" or status_code == 404:
                raise ConnectorValidationError(
                    f"Bucket '{self.bucket_name}' does not exist or cannot be found."
                )

            raise ConnectorValidationError(
                f"Unexpected S3 client error (code={error_code}, status={status_code}): {e}"
            )