def _build_input_tokens_display(self, usage: ChatInvokeUsage, cost: TokenCostCalculated | None) -> str:
		"""Build a clear display of input tokens breakdown with emojis and optional costs"""
		C_YELLOW = '\033[93m'
		C_BLUE = '\033[94m'
		C_RESET = '\033[0m'

		parts = []

		# Always show token breakdown if we have cache information, regardless of cost tracking
		if usage.prompt_cached_tokens or usage.prompt_cache_creation_tokens:
			# Calculate actual new tokens (non-cached)
			new_tokens = usage.prompt_tokens - (usage.prompt_cached_tokens or 0)

			if new_tokens > 0:
				new_tokens_fmt = self._format_tokens(new_tokens)
				if self.include_cost and cost and cost.new_prompt_cost > 0:
					parts.append(f'🆕 {C_YELLOW}{new_tokens_fmt} (${cost.new_prompt_cost:.4f}){C_RESET}')
				else:
					parts.append(f'🆕 {C_YELLOW}{new_tokens_fmt}{C_RESET}')

			if usage.prompt_cached_tokens:
				cached_tokens_fmt = self._format_tokens(usage.prompt_cached_tokens)
				if self.include_cost and cost and cost.prompt_read_cached_cost:
					parts.append(f'💾 {C_BLUE}{cached_tokens_fmt} (${cost.prompt_read_cached_cost:.4f}){C_RESET}')
				else:
					parts.append(f'💾 {C_BLUE}{cached_tokens_fmt}{C_RESET}')

			if usage.prompt_cache_creation_tokens:
				creation_tokens_fmt = self._format_tokens(usage.prompt_cache_creation_tokens)
				if self.include_cost and cost and cost.prompt_cache_creation_cost:
					parts.append(f'🔧 {C_BLUE}{creation_tokens_fmt} (${cost.prompt_cache_creation_cost:.4f}){C_RESET}')
				else:
					parts.append(f'🔧 {C_BLUE}{creation_tokens_fmt}{C_RESET}')

		if not parts:
			# Fallback to simple display when no cache information available
			total_tokens_fmt = self._format_tokens(usage.prompt_tokens)
			if self.include_cost and cost and cost.new_prompt_cost > 0:
				parts.append(f'📥 {C_YELLOW}{total_tokens_fmt} (${cost.new_prompt_cost:.4f}){C_RESET}')
			else:
				parts.append(f'📥 {C_YELLOW}{total_tokens_fmt}{C_RESET}')

		return ' + '.join(parts)