def __init__(self, tensorizer_config: TensorizerConfig):
        for k, v in tensorizer_config.items():
            setattr(self, k, v)
        self.file_obj = tensorizer_config.tensorizer_uri
        self.s3_access_key_id = (
            tensorizer_config.s3_access_key_id or envs.S3_ACCESS_KEY_ID
        )
        self.s3_secret_access_key = (
            tensorizer_config.s3_secret_access_key or envs.S3_SECRET_ACCESS_KEY
        )
        self.s3_endpoint = tensorizer_config.s3_endpoint or envs.S3_ENDPOINT_URL

        self.stream_kwargs = {
            "s3_access_key_id": tensorizer_config.s3_access_key_id,
            "s3_secret_access_key": tensorizer_config.s3_secret_access_key,
            "s3_endpoint": tensorizer_config.s3_endpoint,
            **(tensorizer_config.stream_kwargs or {}),
        }

        self.deserialization_kwargs = {
            "verify_hash": tensorizer_config.verify_hash,
            "encryption": tensorizer_config.encryption_keyfile,
            "num_readers": tensorizer_config.num_readers,
            **(tensorizer_config.deserialization_kwargs or {}),
        }

        if self.encryption_keyfile:
            with open_stream(
                tensorizer_config.encryption_keyfile,
                **self.stream_kwargs,
            ) as stream:
                key = stream.read()
                decryption_params = DecryptionParams.from_key(key)
                self.deserialization_kwargs["encryption"] = decryption_params