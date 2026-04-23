def merge_dicts(a: dict, b: dict, path: tuple[str, ...] = ()):
	for key in b:
		if key in a:
			if isinstance(a[key], dict) and isinstance(b[key], dict):
				merge_dicts(a[key], b[key], path + (str(key),))
			elif isinstance(a[key], list) and isinstance(b[key], list):
				a[key] = a[key] + b[key]
			elif a[key] != b[key]:
				raise Exception('Conflict at ' + '.'.join(path + (str(key),)))
		else:
			a[key] = b[key]
	return a