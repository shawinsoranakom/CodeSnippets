def get_usage_tokens_for_model(self, model: str) -> ModelUsageTokens:
		"""Get usage tokens for a specific model"""
		filtered_usage = [u for u in self.usage_history if u.model == model]

		return ModelUsageTokens(
			model=model,
			prompt_tokens=sum(u.usage.prompt_tokens for u in filtered_usage),
			prompt_cached_tokens=sum(u.usage.prompt_cached_tokens or 0 for u in filtered_usage),
			completion_tokens=sum(u.usage.completion_tokens for u in filtered_usage),
			total_tokens=sum(u.usage.prompt_tokens + u.usage.completion_tokens for u in filtered_usage),
		)