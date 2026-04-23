def _cloud_rest(argv: list[str], version: str) -> int:
	"""Generic REST passthrough."""
	if len(argv) < 2:
		print(f'Usage: browser-use cloud {version} <METHOD> <path> [body]', file=sys.stderr)
		return 1

	method = argv[0].upper()
	path = argv[1]
	body_str = argv[2] if len(argv) > 2 else None

	# Normalize path
	if not path.startswith('/'):
		path = '/' + path

	url = f'{_base_url(version)}{path}'
	api_key = _get_api_key()

	body = body_str.encode() if body_str else None
	status, resp_body = _http_request(method, url, body, api_key)

	if 400 <= status < 500:
		print(f'HTTP {status}', file=sys.stderr)
		_print_json(resp_body, file=sys.stderr)

		# Try to suggest correct body from spec
		spec_data = _fetch_spec(version)
		if spec_data:
			try:
				spec = json.loads(spec_data)
				example = _find_body_example(spec, method, path)
				if example:
					print(f"\nExpected body: '{example}'", file=sys.stderr)
			except (json.JSONDecodeError, ValueError):
				pass
		return 2

	if status >= 500:
		print(f'HTTP {status}', file=sys.stderr)
		_print_json(resp_body, file=sys.stderr)
		return 1

	_print_json(resp_body)
	return 0