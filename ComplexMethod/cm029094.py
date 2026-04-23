def _build_filename_error_message(file_name: str, supported_extensions: list[str]) -> str:
	"""Build a specific error message explaining why the filename was rejected and how to fix it."""
	base = os.path.basename(file_name)

	# Check for binary/image extension
	if '.' in base:
		_, ext = base.rsplit('.', 1)
		ext_lower = ext.lower()
		if ext_lower in UNSUPPORTED_BINARY_EXTENSIONS:
			return (
				f"Error: Cannot write binary/image file '{base}'. "
				f'The write_file tool only supports text-based files. '
				f'Supported extensions: {", ".join("." + e for e in supported_extensions)}. '
				f'For screenshots, the browser automatically captures them - do not try to save screenshots as files.'
			)
		if ext_lower not in supported_extensions:
			return (
				f"Error: Unsupported file extension '.{ext_lower}' in '{base}'. "
				f'Supported extensions: {", ".join("." + e for e in supported_extensions)}. '
				f'Please rename the file to use a supported extension.'
			)

	# No extension or no dot
	if '.' not in base:
		return (
			f"Error: Filename '{base}' has no extension. "
			f'Please add a supported extension: {", ".join("." + e for e in supported_extensions)}.'
		)

	return (
		f"Error: Invalid filename '{base}'. "
		f'Filenames must contain only letters, numbers, underscores, hyphens, dots, parentheses, and spaces. '
		f'Supported extensions: {", ".join("." + e for e in supported_extensions)}.'
	)