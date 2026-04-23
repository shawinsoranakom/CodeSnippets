def get_llm(config: dict[str, Any]):
	"""Get the language model based on config and available API keys."""
	model_config = config.get('model', {})
	model_name = model_config.get('name')
	temperature = model_config.get('temperature', 0.0)

	# Get API key from config or environment
	api_key = model_config.get('api_keys', {}).get('OPENAI_API_KEY') or CONFIG.OPENAI_API_KEY

	if model_name:
		if model_name.startswith('gpt'):
			if not api_key and not CONFIG.OPENAI_API_KEY:
				print('⚠️  OpenAI API key not found. Please update your config or set OPENAI_API_KEY environment variable.')
				sys.exit(1)
			return ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key or CONFIG.OPENAI_API_KEY)
		elif model_name.startswith('claude'):
			if not CONFIG.ANTHROPIC_API_KEY:
				print('⚠️  Anthropic API key not found. Please update your config or set ANTHROPIC_API_KEY environment variable.')
				sys.exit(1)
			return ChatAnthropic(model=model_name, temperature=temperature)
		elif model_name.startswith('gemini'):
			if not CONFIG.GOOGLE_API_KEY:
				print('⚠️  Google API key not found. Please update your config or set GOOGLE_API_KEY environment variable.')
				sys.exit(1)
			return ChatGoogle(model=model_name, temperature=temperature)
		elif model_name.startswith('oci'):
			# OCI models require additional configuration
			print(
				'⚠️  OCI models require manual configuration. Please use the ChatOCIRaw class directly with your OCI credentials.'
			)
			sys.exit(1)

	# Auto-detect based on available API keys
	if api_key or CONFIG.OPENAI_API_KEY:
		return ChatOpenAI(model='gpt-5-mini', temperature=temperature, api_key=api_key or CONFIG.OPENAI_API_KEY)
	elif CONFIG.ANTHROPIC_API_KEY:
		return ChatAnthropic(model='claude-4-sonnet', temperature=temperature)
	elif CONFIG.GOOGLE_API_KEY:
		return ChatGoogle(model='gemini-2.5-pro', temperature=temperature)
	else:
		print(
			'⚠️  No API keys found. Please update your config or set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY.'
		)
		sys.exit(1)