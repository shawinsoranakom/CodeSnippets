def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        """Load credentials"""
        logging.debug(
            f"Loading credentials for {self.bucket_name} of type {self.bucket_type}"
        )

        # Validate credentials
        if self.bucket_type == BlobType.R2:
            if not all( 
                credentials.get(key)
                for key in ["r2_access_key_id", "r2_secret_access_key", "account_id"]
            ):
                raise ConnectorMissingCredentialError("Cloudflare R2")

        elif self.bucket_type == BlobType.S3:
            authentication_method = credentials.get("authentication_method", "access_key")

            if authentication_method == "access_key":
                if not all(
                    credentials.get(key)
                    for key in ["aws_access_key_id", "aws_secret_access_key"]
                ):
                    raise ConnectorMissingCredentialError("Amazon S3")

            elif authentication_method == "iam_role":
                if not credentials.get("aws_role_arn"):
                    raise ConnectorMissingCredentialError("Amazon S3 IAM role ARN is required")

            elif authentication_method == "assume_role":
                pass

            else:
                raise ConnectorMissingCredentialError("Unsupported S3 authentication method")

        elif self.bucket_type == BlobType.GOOGLE_CLOUD_STORAGE:
            if not all(
                credentials.get(key) for key in ["access_key_id", "secret_access_key"]
            ):
                raise ConnectorMissingCredentialError("Google Cloud Storage")

        elif self.bucket_type == BlobType.OCI_STORAGE:
            if not all(
                credentials.get(key)
                for key in ["namespace", "region", "access_key_id", "secret_access_key"]
            ):
                raise ConnectorMissingCredentialError("Oracle Cloud Infrastructure")

        elif self.bucket_type == BlobType.S3_COMPATIBLE:
            if not all(
                credentials.get(key)
                for key in ["endpoint_url", "aws_access_key_id", "aws_secret_access_key", "addressing_style"]
            ):
                raise ConnectorMissingCredentialError("S3 Compatible Storage")

        else:
            raise ValueError(f"Unsupported bucket type: {self.bucket_type}")

        # Create S3 client
        self.s3_client = create_s3_client(
            self.bucket_type, credentials, self.european_residency
        )

        # Detect bucket region (only important for S3)
        if self.bucket_type == BlobType.S3:
            self.bucket_region = detect_bucket_region(self.s3_client, self.bucket_name)

        return None