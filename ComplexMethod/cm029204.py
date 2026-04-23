def format_error(error: Exception, include_trace: bool = False) -> str:
		"""Format error message based on error type and optionally include trace"""
		message = ''
		if isinstance(error, ValidationError):
			return f'{AgentError.VALIDATION_ERROR}\nDetails: {str(error)}'
		# Lazy import to avoid loading openai SDK (~800ms) at module level
		from openai import RateLimitError

		if isinstance(error, RateLimitError):
			return AgentError.RATE_LIMIT_ERROR

		# Handle LLM response validation errors from llm_use
		error_str = str(error)
		if 'LLM response missing required fields' in error_str or 'Expected format: AgentOutput' in error_str:
			# Extract the main error message without the huge stacktrace
			lines = error_str.split('\n')
			main_error = lines[0] if lines else error_str

			# Provide a clearer error message
			helpful_msg = f'{main_error}\n\nThe previous response had an invalid output structure. Please stick to the required output format. \n\n'

			if include_trace:
				helpful_msg += f'\n\nFull stacktrace:\n{traceback.format_exc()}'

			return helpful_msg

		if include_trace:
			return f'{str(error)}\nStacktrace:\n{traceback.format_exc()}'
		return f'{str(error)}'