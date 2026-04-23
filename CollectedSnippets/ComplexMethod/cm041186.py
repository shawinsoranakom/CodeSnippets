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
        Build and return client for connections originating within LocalStack.

        All API operation methods (such as `.list_buckets()` or `.run_instances()`
        take additional args that start with `_` prefix. These are used to pass
        additional information to LocalStack server during internal calls.

        :param service_name: Service to build the client for, eg. `s3`
        :param region_name: Region name. See note above.
            If set to None, loads from botocore session.
        :param aws_access_key_id: Access key to use for the client.
            Defaults to LocalStack internal credentials.
        :param aws_secret_access_key: Secret key to use for the client.
            Defaults to LocalStack internal credentials.
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

        endpoint_url = endpoint_url or self._endpoint or get_service_endpoint()
        if (
            endpoint_url
            and service_name == "s3"
            and re.match(r"https?://localhost(:[0-9]+)?", endpoint_url)
        ):
            endpoint_url = endpoint_url.replace("://localhost", f"://{get_s3_hostname()}")

        return self._get_client(
            service_name=service_name,
            region_name=region_name or self._get_region(),
            use_ssl=self._use_ssl,
            verify=self._verify,
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id or INTERNAL_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=aws_secret_access_key or INTERNAL_AWS_SECRET_ACCESS_KEY,
            aws_session_token=aws_session_token,
            config=config,
        )