async def evaluate(self, page_function: str, *args) -> str:
		"""Execute JavaScript in the target.

		Args:
			page_function: JavaScript code that MUST start with (...args) => format
			*args: Arguments to pass to the function

		Returns:
			String representation of the JavaScript execution result.
			Objects and arrays are JSON-stringified.
		"""
		session_id = await self._ensure_session()

		# Clean and fix common JavaScript string parsing issues
		page_function = self._fix_javascript_string(page_function)

		# Enforce arrow function format
		if not (page_function.startswith('(') and '=>' in page_function):
			raise ValueError(f'JavaScript code must start with (...args) => format. Got: {page_function[:50]}...')

		# Build the expression - call the arrow function with provided args
		if args:
			# Convert args to JSON representation for safe passing
			import json

			arg_strs = [json.dumps(arg) for arg in args]
			expression = f'({page_function})({", ".join(arg_strs)})'
		else:
			expression = f'({page_function})()'

		# Debug: log the actual expression being evaluated
		logger.debug(f'Evaluating JavaScript: {repr(expression)}')

		params: 'EvaluateParameters' = {'expression': expression, 'returnByValue': True, 'awaitPromise': True}
		result = await self._client.send.Runtime.evaluate(
			params,
			session_id=session_id,
		)

		if 'exceptionDetails' in result:
			raise RuntimeError(f'JavaScript evaluation failed: {result["exceptionDetails"]}')

		value = result.get('result', {}).get('value')

		# Always return string representation
		if value is None:
			return ''
		elif isinstance(value, str):
			return value
		else:
			# Convert objects, numbers, booleans to string
			import json

			try:
				return json.dumps(value) if isinstance(value, (dict, list)) else str(value)
			except (TypeError, ValueError):
				return str(value)