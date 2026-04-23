def _get_client_params(self) -> dict[str, Any]:
		_client_params: dict[str, Any] = {}

		self.api_key = self.api_key or os.getenv('AZURE_OPENAI_KEY') or os.getenv('AZURE_OPENAI_API_KEY')
		self.azure_endpoint = self.azure_endpoint or os.getenv('AZURE_OPENAI_ENDPOINT')
		self.azure_deployment = self.azure_deployment or os.getenv('AZURE_OPENAI_DEPLOYMENT')
		params_mapping = {
			'api_key': self.api_key,
			'api_version': self.api_version,
			'organization': self.organization,
			'azure_endpoint': self.azure_endpoint,
			'azure_deployment': self.azure_deployment,
			'base_url': self.base_url,
			'azure_ad_token': self.azure_ad_token,
			'azure_ad_token_provider': self.azure_ad_token_provider,
			'http_client': self.http_client,
		}
		if self.default_headers is not None:
			_client_params['default_headers'] = self.default_headers
		if self.default_query is not None:
			_client_params['default_query'] = self.default_query

		_client_params.update({k: v for k, v in params_mapping.items() if v is not None})

		return _client_params