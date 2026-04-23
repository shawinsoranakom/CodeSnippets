def build_model(self) -> LanguageModel:  # type: ignore[type-var]
        try:
            from langchain_aws import ChatBedrock
        except ImportError as e:
            msg = "langchain_aws is not installed. Please install it with `pip install langchain_aws`."
            raise ImportError(msg) from e
        try:
            import boto3
        except ImportError as e:
            msg = "boto3 is not installed. Please install it with `pip install boto3`."
            raise ImportError(msg) from e
        if self.aws_access_key_id or self.aws_secret_access_key:
            try:
                session = boto3.Session(
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key,
                    aws_session_token=self.aws_session_token,
                )
            except Exception as e:
                msg = "Could not create a boto3 session."
                raise ValueError(msg) from e
        elif self.credentials_profile_name:
            session = boto3.Session(profile_name=self.credentials_profile_name)
        else:
            session = boto3.Session()

        client_params = {}
        if self.endpoint_url:
            client_params["endpoint_url"] = self.endpoint_url
        if self.region_name:
            client_params["region_name"] = self.region_name

        boto3_client = session.client("bedrock-runtime", **client_params)
        try:
            output = ChatBedrock(
                client=boto3_client,
                model_id=self.model_id,
                region_name=self.region_name,
                model_kwargs=self.model_kwargs,
                endpoint_url=self.endpoint_url,
                streaming=self.stream,
            )
        except Exception as e:
            msg = "Could not connect to AmazonBedrock API."
            raise ValueError(msg) from e
        return output