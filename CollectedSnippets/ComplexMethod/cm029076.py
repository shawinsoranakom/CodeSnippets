def _format_choice(name: str, metadata: dict[str, Any], width: int, is_default: bool = False) -> str:
	"""
	Format a template choice with responsive display based on terminal width.

	Styling:
	- Featured templates get [FEATURED] prefix
	- Author name included when width allows (except for default templates)
	- Everything turns orange when highlighted (InquirerPy's built-in behavior)

	Args:
		name: Template name
		metadata: Template metadata (description, featured, author)
		width: Terminal width in columns
		is_default: Whether this is a default template (default, advanced, tools)

	Returns:
		Formatted choice string
	"""
	is_featured = metadata.get('featured', False)
	description = metadata.get('description', '')
	author_name = metadata.get('author', {}).get('name', '') if isinstance(metadata.get('author'), dict) else ''

	# Build the choice string based on terminal width
	if width > 100:
		# Wide: show everything including author (except for default templates)
		if is_featured:
			if author_name:
				return f'[FEATURED] {name} by {author_name} - {description}'
			else:
				return f'[FEATURED] {name} - {description}'
		else:
			# Non-featured templates
			if author_name and not is_default:
				return f'{name} by {author_name} - {description}'
			else:
				return f'{name} - {description}'

	elif width > 60:
		# Medium: show name and description, no author
		if is_featured:
			return f'[FEATURED] {name} - {description}'
		else:
			return f'{name} - {description}'

	else:
		# Narrow: show name only
		return name