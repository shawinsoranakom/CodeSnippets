def _parse_usage(response: Any) -> ChatInvokeUsage | None:
		"""Extract token usage from a litellm response."""
		usage = getattr(response, 'usage', None)
		if usage is None:
			return None

		prompt_tokens = getattr(usage, 'prompt_tokens', 0) or 0
		completion_tokens = getattr(usage, 'completion_tokens', 0) or 0

		prompt_cached = getattr(usage, 'cache_read_input_tokens', None)
		cache_creation = getattr(usage, 'cache_creation_input_tokens', None)

		if prompt_cached is None:
			details = getattr(usage, 'prompt_tokens_details', None)
			if details:
				prompt_cached = getattr(details, 'cached_tokens', None)

		return ChatInvokeUsage(
			prompt_tokens=prompt_tokens,
			prompt_cached_tokens=int(prompt_cached) if prompt_cached is not None else None,
			prompt_cache_creation_tokens=int(cache_creation) if cache_creation is not None else None,
			prompt_image_tokens=None,
			completion_tokens=completion_tokens,
			total_tokens=prompt_tokens + completion_tokens,
		)