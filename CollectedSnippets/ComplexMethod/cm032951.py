def create_s3_client(bucket_type: BlobType, credentials: dict[str, Any], european_residency: bool = False) -> S3Client:
    """Create S3 client for different blob storage types"""
    if bucket_type == BlobType.R2:
        subdomain = "eu." if european_residency else ""
        endpoint_url = f"https://{credentials['account_id']}.{subdomain}r2.cloudflarestorage.com"

        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=credentials["r2_access_key_id"],
            aws_secret_access_key=credentials["r2_secret_access_key"],
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    elif bucket_type == BlobType.S3:
        authentication_method = credentials.get("authentication_method", "access_key")

        region_name = credentials.get("region") or None

        if authentication_method == "access_key":
            session = boto3.Session(
                aws_access_key_id=credentials["aws_access_key_id"],
                aws_secret_access_key=credentials["aws_secret_access_key"],
                region_name=region_name,
            )
            return session.client("s3", region_name=region_name)

        elif authentication_method == "iam_role":
            role_arn = credentials["aws_role_arn"]

            def _refresh_credentials() -> dict[str, str]:
                sts_client = boto3.client("sts", region_name=credentials.get("region") or None)
                assumed_role_object = sts_client.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName=f"onyx_blob_storage_{int(datetime.now().timestamp())}",
                )
                creds = assumed_role_object["Credentials"]
                return {
                    "access_key": creds["AccessKeyId"],
                    "secret_key": creds["SecretAccessKey"],
                    "token": creds["SessionToken"],
                    "expiry_time": creds["Expiration"].isoformat(),
                }

            refreshable = RefreshableCredentials.create_from_metadata(
                metadata=_refresh_credentials(),
                refresh_using=_refresh_credentials,
                method="sts-assume-role",
            )
            botocore_session = get_session()
            botocore_session._credentials = refreshable
            session = boto3.Session(botocore_session=botocore_session, region_name=region_name)
            return session.client("s3", region_name=region_name)

        elif authentication_method == "assume_role":
            return boto3.client("s3", region_name=region_name)

        else:
            raise ValueError("Invalid authentication method for S3.")

    elif bucket_type == BlobType.GOOGLE_CLOUD_STORAGE:
        return boto3.client(
            "s3",
            endpoint_url="https://storage.googleapis.com",
            aws_access_key_id=credentials["access_key_id"],
            aws_secret_access_key=credentials["secret_access_key"],
            region_name="auto",
        )

    elif bucket_type == BlobType.OCI_STORAGE:
        return boto3.client(
            "s3",
            endpoint_url=f"https://{credentials['namespace']}.compat.objectstorage.{credentials['region']}.oraclecloud.com",
            aws_access_key_id=credentials["access_key_id"],
            aws_secret_access_key=credentials["secret_access_key"],
            region_name=credentials["region"],
        )
    elif bucket_type == BlobType.S3_COMPATIBLE:

        return boto3.client(
            "s3",
            endpoint_url=credentials["endpoint_url"],
            aws_access_key_id=credentials["aws_access_key_id"],
            aws_secret_access_key=credentials["aws_secret_access_key"],
            config=Config(s3={'addressing_style': credentials["addressing_style"]}),
        )

    else:
        raise ValueError(f"Unsupported bucket type: {bucket_type}")