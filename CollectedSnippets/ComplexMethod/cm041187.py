def get_client(
        self,
        service_name: str,
        region_name: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_session_token: str | None = None,
        endpoint_url: str | None = None,
        config: Config | None = None,
    ) -> BaseClient:
        """
        Build and return client for connections originating outside LocalStack and targeting Localstack.

        If the region is set to None, it is loaded from following
        locations:
        - AWS environment variables
        - Credentials file `~/.aws/credentials`
        - Config file `~/.aws/config`

        :param service_name: Service to build the client for, eg. `s3`
        :param region_name: Name of the AWS region to be associated with the client
            If set to None, loads from botocore session.
        :param aws_access_key_id: Access key to use for the client.
            If set to None, loads from botocore session.
        :param aws_secret_access_key: Secret key to use for the client.
            If set to None, uses a placeholder value
        :param aws_session_token: Session token to use for the client.
            Not being used if not set.
        :param endpoint_url: Full endpoint URL to be used by the client.
            Defaults to appropriate LocalStack endpoint.
        :param config: Boto config for advanced use.
        """
        if config is None:
            config = self._config
        else:
            config = self._config.merge(config)

        # Boto has an odd behaviour when using a non-default (any other region than us-east-1) in config
        # If the region in arg is non-default, it gives the arg the precedence
        # But if the region in arg is default (us-east-1), it gives precedence to one in config
        # Below: always give precedence to arg region
        if (
            config
            and config.region_name != AWS_REGION_US_EAST_1
            and region_name == AWS_REGION_US_EAST_1
        ):
            config = config.merge(Config(region_name=region_name))

        endpoint_url = endpoint_url or self._endpoint or get_service_endpoint()
        if (
            endpoint_url
            and service_name == "s3"
            and re.match(r"https?://localhost(:[0-9]+)?", endpoint_url)
        ):
            endpoint_url = endpoint_url.replace("://localhost", f"://{get_s3_hostname()}")

        # Prevent `PartialCredentialsError` when only access key ID is provided
        # The value of secret access key is insignificant and can be set to anything
        if aws_access_key_id:
            aws_secret_access_key = aws_secret_access_key or INTERNAL_AWS_SECRET_ACCESS_KEY

        return self._get_client(
            service_name=service_name,
            region_name=region_name or config.region_name or self._get_region(),
            use_ssl=self._use_ssl,
            verify=self._verify,
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            config=config,
        )