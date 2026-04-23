def _normalize_action_for_hash(action_name: str, params: dict[str, Any]) -> str:
	"""Normalize action parameters for similarity hashing.

	For search actions: strip minor keyword variations by sorting tokens.
	For click actions: hash by element type + rough text content, ignoring index.
	For navigate: hash by URL domain only.
	For others: hash by action_name + sorted params.
	"""
	if action_name == 'search':
		query = str(params.get('query', ''))
		# Normalize search: lowercase, sort tokens, collapse whitespace
		tokens = sorted(set(re.sub(r'[^\w\s]', ' ', query.lower()).split()))
		engine = params.get('engine', 'google')
		return f'search|{engine}|{"|".join(tokens)}'

	if action_name in ('click', 'input'):
		# For element-interaction actions, we only use the index (element identity).
		# Two clicks on the same element index are the same action.
		index = params.get('index')
		if action_name == 'input':
			text = str(params.get('text', ''))
			# Normalize input text: lowercase, strip whitespace
			return f'input|{index}|{text.strip().lower()}'
		return f'click|{index}'

	if action_name == 'navigate':
		url = str(params.get('url', ''))
		# Hash by full URL — navigating to different paths is genuine exploration,
		# only repeated navigation to the exact same URL is a loop signal.
		return f'navigate|{url}'

	if action_name == 'scroll':
		direction = 'down' if params.get('down', True) else 'up'
		index = params.get('index')
		return f'scroll|{direction}|{index}'

	# Default: hash by action name + sorted params (excluding None values)
	filtered = {k: v for k, v in sorted(params.items()) if v is not None}
	return f'{action_name}|{json.dumps(filtered, sort_keys=True, default=str)}'