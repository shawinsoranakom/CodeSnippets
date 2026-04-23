def _get_client(self) -> 'AwsClient':  # type: ignore
		"""Get the AWS Bedrock client."""
		try:
			from boto3 import client as AwsClient  # type: ignore
		except ImportError:
			raise ImportError(
				'`boto3` not installed. Please install using `pip install browser-use[aws] or pip install browser-use[all]`'
			)

		if self.session:
			return self.session.client('bedrock-runtime')

		# Get credentials from environment or instance parameters
		access_key = self.aws_access_key_id or getenv('AWS_ACCESS_KEY_ID')
		secret_key = self.aws_secret_access_key or getenv('AWS_SECRET_ACCESS_KEY')
		session_token = self.aws_session_token or getenv('AWS_SESSION_TOKEN')
		region = self.aws_region or getenv('AWS_REGION') or getenv('AWS_DEFAULT_REGION')

		if self.aws_sso_auth:
			return AwsClient(service_name='bedrock-runtime', region_name=region)
		else:
			if not access_key or not secret_key:
				raise ModelProviderError(
					message='AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables (and AWS_SESSION_TOKEN if using temporary credentials) or provide a boto3 session.',
					model=self.name,
				)

			return AwsClient(
				service_name='bedrock-runtime',
				region_name=region,
				aws_access_key_id=access_key,
				aws_secret_access_key=secret_key,
				aws_session_token=session_token,
			)