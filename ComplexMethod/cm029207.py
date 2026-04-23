def _detect_from_attributes(attributes: dict[str, str]) -> tuple[str, str | None] | None:
	"""
	Detect variable from element attributes.

	Check attributes in priority order:
	1. type attribute (HTML5 input types - most specific)
	2. id, name, placeholder, aria-label (semantic hints)
	"""

	# Check 'type' attribute first (HTML5 input types)
	input_type = attributes.get('type', '').lower()
	if input_type == 'email':
		return ('email', 'email')
	elif input_type == 'tel':
		return ('phone', 'phone')
	elif input_type == 'date':
		return ('date', 'date')
	elif input_type == 'number':
		return ('number', 'number')
	elif input_type == 'url':
		return ('url', 'url')

	# Combine semantic attributes for keyword matching
	semantic_attrs = [
		attributes.get('id', ''),
		attributes.get('name', ''),
		attributes.get('placeholder', ''),
		attributes.get('aria-label', ''),
	]

	combined_text = ' '.join(semantic_attrs).lower()

	# Address detection
	if any(keyword in combined_text for keyword in ['address', 'street', 'addr']):
		if 'billing' in combined_text:
			return ('billing_address', None)
		elif 'shipping' in combined_text:
			return ('shipping_address', None)
		else:
			return ('address', None)

	# Comment/Note detection
	if any(keyword in combined_text for keyword in ['comment', 'note', 'message', 'description']):
		return ('comment', None)

	# Email detection
	if 'email' in combined_text or 'e-mail' in combined_text:
		return ('email', 'email')

	# Phone detection
	if any(keyword in combined_text for keyword in ['phone', 'tel', 'mobile', 'cell']):
		return ('phone', 'phone')

	# Name detection (order matters - check specific before general)
	if 'first' in combined_text and 'name' in combined_text:
		return ('first_name', None)
	elif 'last' in combined_text and 'name' in combined_text:
		return ('last_name', None)
	elif 'full' in combined_text and 'name' in combined_text:
		return ('full_name', None)
	elif 'name' in combined_text:
		return ('name', None)

	# Date detection
	if any(keyword in combined_text for keyword in ['date', 'dob', 'birth']):
		return ('date', 'date')

	# City detection
	if 'city' in combined_text:
		return ('city', None)

	# State/Province detection
	if 'state' in combined_text or 'province' in combined_text:
		return ('state', None)

	# Country detection
	if 'country' in combined_text:
		return ('country', None)

	# Zip code detection
	if any(keyword in combined_text for keyword in ['zip', 'postal', 'postcode']):
		return ('zip_code', 'postal_code')

	# Company detection
	if 'company' in combined_text or 'organization' in combined_text:
		return ('company', None)

	return None