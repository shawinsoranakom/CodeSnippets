def _get_client_params(self) -> dict[str, Any]:
		"""Prepare client parameters dictionary for Bedrock."""
		client_params: dict[str, Any] = {}

		if self.session:
			credentials = self.session.get_credentials()
			client_params.update(
				{
					'aws_access_key': credentials.access_key,
					'aws_secret_key': credentials.secret_key,
					'aws_session_token': credentials.token,
					'aws_region': self.session.region_name,
				}
			)
		else:
			# Use individual credentials
			if self.aws_access_key:
				client_params['aws_access_key'] = self.aws_access_key
			if self.aws_secret_key:
				client_params['aws_secret_key'] = self.aws_secret_key
			if self.aws_region:
				client_params['aws_region'] = self.aws_region
			if self.aws_session_token:
				client_params['aws_session_token'] = self.aws_session_token

		# Add optional parameters
		if self.max_retries:
			client_params['max_retries'] = self.max_retries
		if self.default_headers:
			client_params['default_headers'] = self.default_headers
		if self.default_query:
			client_params['default_query'] = self.default_query

		return client_params