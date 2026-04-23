async def evaluate(self, page_function: str, *args) -> str:
		"""Execute JavaScript code in the context of this element.

		The JavaScript code executes with 'this' bound to the element, allowing direct
		access to element properties and methods.

		Args:
			page_function: JavaScript code that MUST start with (...args) => format
			*args: Arguments to pass to the function

		Returns:
			String representation of the JavaScript execution result.
			Objects and arrays are JSON-stringified.

		Example:
			# Get element's text content
			text = await element.evaluate("() => this.textContent")

			# Set style with argument
			await element.evaluate("(color) => this.style.color = color", "red")

			# Get computed style
			color = await element.evaluate("() => getComputedStyle(this).color")

			# Async operations
			result = await element.evaluate("async () => { await new Promise(r => setTimeout(r, 100)); return this.id; }")
		"""
		# Get remote object ID for this element
		object_id = await self._get_remote_object_id()
		if not object_id:
			raise RuntimeError('Element has no remote object ID (element may be detached from DOM)')

		# Validate arrow function format (allow async prefix)
		page_function = page_function.strip()
		# Check for arrow function with optional async prefix
		if not ('=>' in page_function and (page_function.startswith('(') or page_function.startswith('async'))):
			raise ValueError(
				f'JavaScript code must start with (...args) => or async (...args) => format. Got: {page_function[:50]}...'
			)

		# Convert arrow function to function declaration for CallFunctionOn
		# CallFunctionOn expects 'function(...args) { ... }' format, not arrow functions
		# We need to convert: '() => expression' to 'function() { return expression; }'
		# or: '(x, y) => { statements }' to 'function(x, y) { statements }'

		# Extract parameters and body from arrow function
		import re

		# Check if it's an async arrow function
		is_async = page_function.strip().startswith('async')
		async_prefix = 'async ' if is_async else ''

		# Match: (params) => body  or  async (params) => body
		# Strip 'async' prefix if present for parsing
		func_to_parse = page_function.strip()
		if is_async:
			func_to_parse = func_to_parse[5:].strip()  # Remove 'async' prefix

		arrow_match = re.match(r'\s*\(([^)]*)\)\s*=>\s*(.+)', func_to_parse, re.DOTALL)
		if not arrow_match:
			raise ValueError(f'Could not parse arrow function: {page_function[:50]}...')

		params_str = arrow_match.group(1).strip()  # e.g., '', 'x', 'x, y'
		body = arrow_match.group(2).strip()

		# If body doesn't start with {, it's an expression that needs implicit return
		if not body.startswith('{'):
			function_declaration = f'{async_prefix}function({params_str}) {{ return {body}; }}'
		else:
			# Body already has braces, use as-is
			function_declaration = f'{async_prefix}function({params_str}) {body}'

		# Build CallArgument list for args if provided
		call_arguments = []
		if args:
			from cdp_use.cdp.runtime.types import CallArgument

			for arg in args:
				# Convert Python values to CallArgument format
				call_arguments.append(CallArgument(value=arg))

		# Prepare CallFunctionOn parameters

		params: 'CallFunctionOnParameters' = {
			'functionDeclaration': function_declaration,
			'objectId': object_id,
			'returnByValue': True,
			'awaitPromise': True,
		}

		if call_arguments:
			params['arguments'] = call_arguments

		# Execute the function on the element
		result = await self._client.send.Runtime.callFunctionOn(
			params,
			session_id=self._session_id,
		)

		# Handle exceptions
		if 'exceptionDetails' in result:
			raise RuntimeError(f'JavaScript evaluation failed: {result["exceptionDetails"]}')

		# Extract and return value
		value = result.get('result', {}).get('value')

		# Return string representation (matching Page.evaluate behavior)
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