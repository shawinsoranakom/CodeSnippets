def __getattr__(self, name: str) -> Any:
		"""Dynamically proxy all attributes to fresh instances.

		This ensures env vars are re-read on every access.
		"""
		# Special handling for internal attributes
		if name.startswith('_'):
			raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

		# Create fresh instances on every access
		old_config = OldConfig()

		# Always use old config for all attributes (it handles env vars with proper transformations)
		if hasattr(old_config, name):
			return getattr(old_config, name)

		# For new MCP-specific attributes not in old config
		env_config = FlatEnvConfig()
		if hasattr(env_config, name):
			return getattr(env_config, name)

		# Handle special methods
		if name == 'get_default_profile':
			return lambda: self._get_default_profile()
		elif name == 'get_default_llm':
			return lambda: self._get_default_llm()
		elif name == 'get_default_agent':
			return lambda: self._get_default_agent()
		elif name == 'load_config':
			return lambda: self._load_config()
		elif name == '_ensure_dirs':
			return lambda: old_config._ensure_dirs()

		raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")