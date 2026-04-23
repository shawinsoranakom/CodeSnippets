def load_and_migrate_config(config_path: Path) -> DBStyleConfigJSON:
	"""Load config.json or create fresh one if old format detected."""
	if not config_path.exists():
		# Create fresh config with defaults
		config_path.parent.mkdir(parents=True, exist_ok=True)
		new_config = create_default_config()
		with open(config_path, 'w') as f:
			json.dump(new_config.model_dump(), f, indent=2)
		return new_config

	try:
		with open(config_path) as f:
			data = json.load(f)

		# Check if it's already in DB-style format
		if all(key in data for key in ['browser_profile', 'llm', 'agent']) and all(
			isinstance(data.get(key, {}), dict) for key in ['browser_profile', 'llm', 'agent']
		):
			# Check if the values are DB-style entries (have UUIDs as keys)
			if data.get('browser_profile') and all(isinstance(v, dict) and 'id' in v for v in data['browser_profile'].values()):
				# Already in new format
				return DBStyleConfigJSON(**data)

		# Old format detected - delete it and create fresh config
		logger.debug(f'Old config format detected at {config_path}, creating fresh config')
		new_config = create_default_config()

		# Overwrite with new config
		with open(config_path, 'w') as f:
			json.dump(new_config.model_dump(), f, indent=2)

		logger.debug(f'Created fresh config.json at {config_path}')
		return new_config

	except Exception as e:
		logger.error(f'Failed to load config from {config_path}: {e}, creating fresh config')
		# On any error, create fresh config
		new_config = create_default_config()
		try:
			with open(config_path, 'w') as f:
				json.dump(new_config.model_dump(), f, indent=2)
		except Exception as write_error:
			logger.error(f'Failed to write fresh config: {write_error}')
		return new_config