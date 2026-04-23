def _load_config(self) -> dict[str, Any]:
		"""Load configuration with env var overrides for MCP components."""
		config = {
			'browser_profile': self._get_default_profile(),
			'llm': self._get_default_llm(),
			'agent': self._get_default_agent(),
		}

		# Fresh env config for overrides
		env_config = FlatEnvConfig()

		# Apply MCP-specific env var overrides
		if env_config.BROWSER_USE_HEADLESS is not None:
			config['browser_profile']['headless'] = env_config.BROWSER_USE_HEADLESS

		if env_config.BROWSER_USE_ALLOWED_DOMAINS:
			domains = [d.strip() for d in env_config.BROWSER_USE_ALLOWED_DOMAINS.split(',') if d.strip()]
			config['browser_profile']['allowed_domains'] = domains

		# Proxy settings (Chromium) -> consolidated `proxy` dict
		proxy_dict: dict[str, Any] = {}
		if env_config.BROWSER_USE_PROXY_URL:
			proxy_dict['server'] = env_config.BROWSER_USE_PROXY_URL
		if env_config.BROWSER_USE_NO_PROXY:
			# store bypass as comma-separated string to match Chrome flag
			proxy_dict['bypass'] = ','.join([d.strip() for d in env_config.BROWSER_USE_NO_PROXY.split(',') if d.strip()])
		if env_config.BROWSER_USE_PROXY_USERNAME:
			proxy_dict['username'] = env_config.BROWSER_USE_PROXY_USERNAME
		if env_config.BROWSER_USE_PROXY_PASSWORD:
			proxy_dict['password'] = env_config.BROWSER_USE_PROXY_PASSWORD
		if proxy_dict:
			# ensure section exists
			config.setdefault('browser_profile', {})
			config['browser_profile']['proxy'] = proxy_dict

		if env_config.OPENAI_API_KEY:
			config['llm']['api_key'] = env_config.OPENAI_API_KEY

		if env_config.BROWSER_USE_LLM_MODEL:
			config['llm']['model'] = env_config.BROWSER_USE_LLM_MODEL

		# Extension settings
		if env_config.BROWSER_USE_DISABLE_EXTENSIONS is not None:
			config['browser_profile']['enable_default_extensions'] = not env_config.BROWSER_USE_DISABLE_EXTENSIONS

		return config