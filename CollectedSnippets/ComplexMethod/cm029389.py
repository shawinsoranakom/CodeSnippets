async def log_usage_summary(self) -> None:
		"""Log a comprehensive usage summary per model with colors and nice formatting"""
		if not self.usage_history:
			return

		summary = await self.get_usage_summary()

		if summary.entry_count == 0:
			return

		# ANSI color codes
		C_CYAN = '\033[96m'
		C_YELLOW = '\033[93m'
		C_GREEN = '\033[92m'
		C_BLUE = '\033[94m'
		C_MAGENTA = '\033[95m'
		C_RESET = '\033[0m'
		C_BOLD = '\033[1m'

		# Log overall summary
		total_tokens_fmt = self._format_tokens(summary.total_tokens)
		prompt_tokens_fmt = self._format_tokens(summary.total_prompt_tokens)
		completion_tokens_fmt = self._format_tokens(summary.total_completion_tokens)

		# Format cost breakdowns for input and output (only if cost tracking is enabled)
		if self.include_cost and summary.total_cost > 0:
			total_cost_part = f' (${C_MAGENTA}{summary.total_cost:.4f}{C_RESET})'
			prompt_cost_part = f' (${summary.total_prompt_cost:.4f})'
			completion_cost_part = f' (${summary.total_completion_cost:.4f})'
		else:
			total_cost_part = ''
			prompt_cost_part = ''
			completion_cost_part = ''

		if len(summary.by_model) > 1:
			cost_logger.debug(
				f'💲 {C_BOLD}Total Usage Summary{C_RESET}: {C_BLUE}{total_tokens_fmt} tokens{C_RESET}{total_cost_part} | '
				f'⬅️ {C_YELLOW}{prompt_tokens_fmt}{prompt_cost_part}{C_RESET} | ➡️ {C_GREEN}{completion_tokens_fmt}{completion_cost_part}{C_RESET}'
			)

		for model, stats in summary.by_model.items():
			# Format tokens
			model_total_fmt = self._format_tokens(stats.total_tokens)
			model_prompt_fmt = self._format_tokens(stats.prompt_tokens)
			model_completion_fmt = self._format_tokens(stats.completion_tokens)
			avg_tokens_fmt = self._format_tokens(int(stats.average_tokens_per_invocation))

			# Format cost display (only if cost tracking is enabled)
			if self.include_cost:
				# Calculate per-model costs on-the-fly
				total_model_cost = 0.0
				model_prompt_cost = 0.0
				model_completion_cost = 0.0

				# Calculate costs for this model
				for entry in self.usage_history:
					if entry.model == model:
						cost = await self.calculate_cost(entry.model, entry.usage)
						if cost:
							model_prompt_cost += cost.prompt_cost
							model_completion_cost += cost.completion_cost

				total_model_cost = model_prompt_cost + model_completion_cost

				if total_model_cost > 0:
					cost_part = f' (${C_MAGENTA}{total_model_cost:.4f}{C_RESET})'
					prompt_part = f'{C_YELLOW}{model_prompt_fmt} (${model_prompt_cost:.4f}){C_RESET}'
					completion_part = f'{C_GREEN}{model_completion_fmt} (${model_completion_cost:.4f}){C_RESET}'
				else:
					cost_part = ''
					prompt_part = f'{C_YELLOW}{model_prompt_fmt}{C_RESET}'
					completion_part = f'{C_GREEN}{model_completion_fmt}{C_RESET}'
			else:
				cost_part = ''
				prompt_part = f'{C_YELLOW}{model_prompt_fmt}{C_RESET}'
				completion_part = f'{C_GREEN}{model_completion_fmt}{C_RESET}'

			cost_logger.debug(
				f'  🤖 {C_CYAN}{model}{C_RESET}: {C_BLUE}{model_total_fmt} tokens{C_RESET}{cost_part} | '
				f'⬅️ {prompt_part} | ➡️ {completion_part} | '
				f'📞 {stats.invocations} calls | 📈 {avg_tokens_fmt}/call'
			)