def _detect_from_value_pattern(value: str) -> tuple[str, str | None] | None:
	"""
	Detect variable type from value pattern (fallback when no element context).

	Patterns:
	- Email: contains @ and . with valid format
	- Phone: digits with separators, 10+ chars
	- Date: YYYY-MM-DD format
	- Name: Capitalized word(s), 2-30 chars, letters only
	- Number: Pure digits, 1-9 chars
	"""

	# Email detection - most specific first
	if '@' in value and '.' in value:
		# Basic email validation
		if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value):
			return ('email', 'email')

	# Phone detection (digits with separators, 10+ chars)
	if re.match(r'^[\d\s\-\(\)\+]+$', value):
		# Remove separators and check length
		digits_only = re.sub(r'[\s\-\(\)\+]', '', value)
		if len(digits_only) >= 10:
			return ('phone', 'phone')

	# Date detection (YYYY-MM-DD or similar)
	if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
		return ('date', 'date')

	# Name detection (capitalized, only letters/spaces, 2-30 chars)
	if value and value[0].isupper() and value.replace(' ', '').replace('-', '').isalpha() and 2 <= len(value) <= 30:
		words = value.split()
		if len(words) == 1:
			return ('first_name', None)
		elif len(words) == 2:
			return ('full_name', None)
		else:
			return ('name', None)

	# Number detection (pure digits, not phone length)
	if value.isdigit() and 1 <= len(value) <= 9:
		return ('number', 'number')

	return None