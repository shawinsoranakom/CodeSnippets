def _fix_javascript_string(self, js_code: str) -> str:
		"""Fix common JavaScript string parsing issues when written as Python string."""

		# Just do minimal, safe cleaning
		js_code = js_code.strip()

		# Only fix the most common and safe issues:

		# 1. Remove obvious Python string wrapper quotes if they exist
		if (js_code.startswith('"') and js_code.endswith('"')) or (js_code.startswith("'") and js_code.endswith("'")):
			# Check if it's a wrapped string (not part of JS syntax)
			inner = js_code[1:-1]
			if inner.count('"') + inner.count("'") == 0 or '() =>' in inner:
				js_code = inner

		# 2. Only fix clearly escaped quotes that shouldn't be
		# But be very conservative - only if we're sure it's a Python string artifact
		if '\\"' in js_code and js_code.count('\\"') > js_code.count('"'):
			js_code = js_code.replace('\\"', '"')
		if "\\'" in js_code and js_code.count("\\'") > js_code.count("'"):
			js_code = js_code.replace("\\'", "'")

		# 3. Basic whitespace normalization only
		js_code = js_code.strip()

		# Final validation - ensure it's not empty
		if not js_code:
			raise ValueError('JavaScript code is empty after cleaning')

		return js_code