async def calculate_cost(self, model: str, usage: ChatInvokeUsage) -> TokenCostCalculated | None:
		if not self.include_cost:
			return None

		data = await self.get_model_pricing(model)
		if data is None:
			return None

		uncached_prompt_tokens = usage.prompt_tokens - (usage.prompt_cached_tokens or 0)

		return TokenCostCalculated(
			new_prompt_tokens=usage.prompt_tokens,
			new_prompt_cost=uncached_prompt_tokens * (data.input_cost_per_token or 0),
			# Cached tokens
			prompt_read_cached_tokens=usage.prompt_cached_tokens,
			prompt_read_cached_cost=usage.prompt_cached_tokens * data.cache_read_input_token_cost
			if usage.prompt_cached_tokens and data.cache_read_input_token_cost
			else None,
			# Cache creation tokens
			prompt_cached_creation_tokens=usage.prompt_cache_creation_tokens,
			prompt_cache_creation_cost=usage.prompt_cache_creation_tokens * data.cache_creation_input_token_cost
			if data.cache_creation_input_token_cost and usage.prompt_cache_creation_tokens
			else None,
			# Completion tokens
			completion_tokens=usage.completion_tokens,
			completion_cost=usage.completion_tokens * float(data.output_cost_per_token or 0),
		)