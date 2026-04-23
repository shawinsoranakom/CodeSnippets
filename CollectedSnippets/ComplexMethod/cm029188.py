def _fix_control_characters_in_json(content: str) -> str:
	"""Fix control characters in JSON string values to make them valid JSON."""
	try:
		# First try to parse as-is to see if it's already valid
		json.loads(content)
		return content
	except json.JSONDecodeError:
		pass

	# More sophisticated approach: only escape control characters inside string values
	# while preserving JSON structure formatting

	result = []
	i = 0
	in_string = False
	escaped = False

	while i < len(content):
		char = content[i]

		if not in_string:
			# Outside of string - check if we're entering a string
			if char == '"':
				in_string = True
			result.append(char)
		else:
			# Inside string - handle escaping and control characters
			if escaped:
				# Previous character was backslash, so this character is escaped
				result.append(char)
				escaped = False
			elif char == '\\':
				# This is an escape character
				result.append(char)
				escaped = True
			elif char == '"':
				# End of string
				result.append(char)
				in_string = False
			elif char == '\n':
				# Literal newline inside string - escape it
				result.append('\\n')
			elif char == '\r':
				# Literal carriage return inside string - escape it
				result.append('\\r')
			elif char == '\t':
				# Literal tab inside string - escape it
				result.append('\\t')
			elif char == '\b':
				# Literal backspace inside string - escape it
				result.append('\\b')
			elif char == '\f':
				# Literal form feed inside string - escape it
				result.append('\\f')
			elif ord(char) < 32:
				# Other control characters inside string - convert to unicode escape
				result.append(f'\\u{ord(char):04x}')
			else:
				# Normal character inside string
				result.append(char)

		i += 1

	return ''.join(result)