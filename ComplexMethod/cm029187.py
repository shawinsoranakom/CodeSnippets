def try_parse_groq_failed_generation(
	error: APIStatusError,
	output_format: type[T],
) -> T:
	"""Extract JSON from model output, handling both plain JSON and code-block-wrapped JSON."""
	try:
		content = error.body['error']['failed_generation']  # type: ignore

		# If content is wrapped in code blocks, extract just the JSON part
		if '```' in content:
			# Find the JSON content between code blocks
			content = content.split('```')[1]
			# Remove language identifier if present (e.g., 'json\n')
			if '\n' in content:
				content = content.split('\n', 1)[1]

		# remove html-like tags before the first { and after the last }
		# This handles cases like <|header_start|>assistant<|header_end|> and <function=AgentOutput>
		# Only remove content before { if content doesn't already start with {
		if not content.strip().startswith('{'):
			content = re.sub(r'^.*?(?=\{)', '', content, flags=re.DOTALL)

		# Remove common HTML-like tags and patterns at the end, but be more conservative
		# Look for patterns like </function>, <|header_start|>, etc. after the JSON
		content = re.sub(r'\}(\s*<[^>]*>.*?$)', '}', content, flags=re.DOTALL)
		content = re.sub(r'\}(\s*<\|[^|]*\|>.*?$)', '}', content, flags=re.DOTALL)

		# Handle extra characters after the JSON, including stray braces
		# Find the position of the last } that would close the main JSON object
		content = content.strip()

		if content.endswith('}'):
			# Try to parse and see if we get valid JSON
			try:
				json.loads(content)
			except json.JSONDecodeError:
				# If parsing fails, try to find the correct end of the JSON
				# by counting braces and removing anything after the balanced JSON
				brace_count = 0
				last_valid_pos = -1
				for i, char in enumerate(content):
					if char == '{':
						brace_count += 1
					elif char == '}':
						brace_count -= 1
						if brace_count == 0:
							last_valid_pos = i + 1
							break

				if last_valid_pos > 0:
					content = content[:last_valid_pos]

		# Fix control characters in JSON strings before parsing
		# This handles cases where literal control characters appear in JSON values
		content = _fix_control_characters_in_json(content)

		# Parse the cleaned content
		result_dict = json.loads(content)

		# some models occasionally respond with a list containing one dict: https://github.com/browser-use/browser-use/issues/1458
		if isinstance(result_dict, list) and len(result_dict) == 1 and isinstance(result_dict[0], dict):
			result_dict = result_dict[0]

		logger.debug(f'Successfully parsed model output: {result_dict}')
		return output_format.model_validate(result_dict)

	except KeyError as e:
		raise ParseFailedGenerationError(e) from e

	except json.JSONDecodeError as e:
		logger.warning(f'Failed to parse model output: {content} {str(e)}')
		raise ValueError(f'Could not parse response. {str(e)}')

	except Exception as e:
		raise ParseFailedGenerationError(error.response.text) from e