def __getattr__(name: str) -> 'BaseChatModel':
	"""Create model instances on demand with API keys from environment."""
	# Handle chat classes first
	if name == 'ChatOpenAI':
		return ChatOpenAI  # type: ignore
	elif name == 'ChatAzureOpenAI':
		return ChatAzureOpenAI  # type: ignore
	elif name == 'ChatGoogle':
		return ChatGoogle  # type: ignore

	elif name == 'ChatMistral':
		return ChatMistral  # type: ignore

	elif name == 'ChatOCIRaw':
		if not OCI_AVAILABLE:
			raise ImportError('OCI integration not available. Install with: pip install "browser-use[oci]"')
		return ChatOCIRaw  # type: ignore
	elif name == 'ChatCerebras':
		return ChatCerebras  # type: ignore
	elif name == 'ChatBrowserUse':
		return ChatBrowserUse  # type: ignore

	# Handle model instances - these are the main use case
	try:
		return get_llm_by_name(name)
	except ValueError:
		raise AttributeError(f"module '{__name__}' has no attribute '{name}'")