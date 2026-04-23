async def get_usage_summary(self, model: str | None = None, since: datetime | None = None) -> UsageSummary:
		"""Get summary of token usage and costs (costs calculated on-the-fly)"""
		filtered_usage = self.usage_history

		if model:
			filtered_usage = [u for u in filtered_usage if u.model == model]

		if since:
			filtered_usage = [u for u in filtered_usage if u.timestamp >= since]

		if not filtered_usage:
			return UsageSummary(
				total_prompt_tokens=0,
				total_prompt_cost=0.0,
				total_prompt_cached_tokens=0,
				total_prompt_cached_cost=0.0,
				total_completion_tokens=0,
				total_completion_cost=0.0,
				total_tokens=0,
				total_cost=0.0,
				entry_count=0,
			)

		# Calculate totals
		total_prompt = sum(u.usage.prompt_tokens for u in filtered_usage)
		total_completion = sum(u.usage.completion_tokens for u in filtered_usage)
		total_tokens = total_prompt + total_completion
		total_prompt_cached = sum(u.usage.prompt_cached_tokens or 0 for u in filtered_usage)

		# Calculate per-model stats with record-by-record cost calculation
		model_stats: dict[str, ModelUsageStats] = {}
		total_prompt_cost = 0.0
		total_completion_cost = 0.0
		total_prompt_cached_cost = 0.0

		for entry in filtered_usage:
			if entry.model not in model_stats:
				model_stats[entry.model] = ModelUsageStats(model=entry.model)

			stats = model_stats[entry.model]
			stats.prompt_tokens += entry.usage.prompt_tokens
			stats.completion_tokens += entry.usage.completion_tokens
			stats.total_tokens += entry.usage.prompt_tokens + entry.usage.completion_tokens
			stats.invocations += 1

			if self.include_cost:
				# Calculate cost record by record using the updated calculate_cost function
				cost = await self.calculate_cost(entry.model, entry.usage)
				if cost:
					stats.cost += cost.total_cost
					total_prompt_cost += cost.prompt_cost
					total_completion_cost += cost.completion_cost
					total_prompt_cached_cost += cost.prompt_read_cached_cost or 0

		# Calculate averages
		for stats in model_stats.values():
			if stats.invocations > 0:
				stats.average_tokens_per_invocation = stats.total_tokens / stats.invocations

		return UsageSummary(
			total_prompt_tokens=total_prompt,
			total_prompt_cost=total_prompt_cost,
			total_prompt_cached_tokens=total_prompt_cached,
			total_prompt_cached_cost=total_prompt_cached_cost,
			total_completion_tokens=total_completion,
			total_completion_cost=total_completion_cost,
			total_tokens=total_tokens,
			total_cost=total_prompt_cost + total_completion_cost + total_prompt_cached_cost,
			entry_count=len(filtered_usage),
			by_model=model_stats,
		)