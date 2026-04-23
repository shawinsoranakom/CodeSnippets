def main(
	template: str | None,
	output: str | None,
	force: bool,
	list_templates: bool,
):
	"""
	Generate a browser-use template file to get started quickly.

	Examples:

	\b
	# Interactive mode - prompts for template selection
	uvx browser-use init
	uvx browser-use init --template

	\b
	# Generate default template
	uvx browser-use init --template default

	\b
	# Generate advanced template with custom filename
	uvx browser-use init --template advanced --output my_script.py

	\b
	# List available templates
	uvx browser-use init --list
	"""

	# Fetch template list at runtime
	try:
		INIT_TEMPLATES = _get_template_list()
	except FileNotFoundError as e:
		console.print(f'[red]✗[/red] {e}')
		sys.exit(1)

	# Handle --list flag
	if list_templates:
		console.print('\n[bold]Available templates:[/bold]\n')
		for name, info in INIT_TEMPLATES.items():
			console.print(f'  [#fe750e]{name:12}[/#fe750e] - {info["description"]}')
		console.print()
		return

	# Interactive template selection if not provided
	if not template:
		# Get terminal width for responsive formatting
		width = _get_terminal_width()

		# Separate default and featured templates
		default_template_names = ['default', 'advanced', 'tools']
		featured_templates = [(name, info) for name, info in INIT_TEMPLATES.items() if info.get('featured', False)]
		other_templates = [
			(name, info)
			for name, info in INIT_TEMPLATES.items()
			if name not in default_template_names and not info.get('featured', False)
		]

		# Sort by last_modified_date (most recent first)
		def get_last_modified(item):
			name, info = item
			date_str = (
				info.get('author', {}).get('last_modified_date', '1970-01-01')
				if isinstance(info.get('author'), dict)
				else '1970-01-01'
			)
			return date_str

		# Sort default templates by last modified
		default_templates = [(name, INIT_TEMPLATES[name]) for name in default_template_names if name in INIT_TEMPLATES]
		default_templates.sort(key=get_last_modified, reverse=True)

		# Sort featured and other templates by last modified
		featured_templates.sort(key=get_last_modified, reverse=True)
		other_templates.sort(key=get_last_modified, reverse=True)

		# Build choices in order: defaults first, then featured, then others
		choices = []

		# Add default templates
		for i, (name, info) in enumerate(default_templates):
			formatted = _format_choice(name, info, width, is_default=True)
			choices.append(Choice(name=formatted, value=name))

		# Add featured templates
		for i, (name, info) in enumerate(featured_templates):
			formatted = _format_choice(name, info, width, is_default=False)
			choices.append(Choice(name=formatted, value=name))

		# Add other templates (if any)
		for name, info in other_templates:
			formatted = _format_choice(name, info, width, is_default=False)
			choices.append(Choice(name=formatted, value=name))

		# Use fuzzy prompt for search functionality
		# Use getattr to avoid static analysis complaining about non-exported names
		_fuzzy = getattr(inquirer, 'fuzzy')
		template = _fuzzy(
			message='Select a template (type to search):',
			choices=choices,
			style=inquirer_style,
			max_height='70%',
		).execute()

		# Handle user cancellation (Ctrl+C)
		if template is None:
			console.print('\n[red]✗[/red] Cancelled')
			sys.exit(1)

	# Template is guaranteed to be set at this point (either from option or prompt)
	assert template is not None

	# Create template directory
	template_dir = Path.cwd() / template
	if template_dir.exists() and not force:
		console.print(f'[yellow]⚠[/yellow]  Directory already exists: [cyan]{template_dir}[/cyan]')
		if not click.confirm('Continue and overwrite files?', default=False):
			console.print('[red]✗[/red] Cancelled')
			sys.exit(1)

	# Create directory
	template_dir.mkdir(parents=True, exist_ok=True)

	# Determine output path
	if output:
		output_path = template_dir / Path(output)
	else:
		output_path = template_dir / 'main.py'

	# Read template file from GitHub
	try:
		template_file = INIT_TEMPLATES[template]['file']
		content = _get_template_content(template_file)
	except Exception as e:
		console.print(f'[red]✗[/red] Error reading template: {e}')
		sys.exit(1)

	# Write file
	if _write_init_file(output_path, content, force):
		console.print(f'\n[green]✓[/green] Created [cyan]{output_path}[/cyan]')

		# Generate additional files if template has a manifest
		if 'files' in INIT_TEMPLATES[template]:
			import stat

			for file_spec in INIT_TEMPLATES[template]['files']:
				source_path = file_spec['source']
				dest_name = file_spec['dest']
				dest_path = output_path.parent / dest_name
				is_binary = file_spec.get('binary', False)
				is_executable = file_spec.get('executable', False)

				# Skip if we already wrote this file (main.py)
				if dest_path == output_path:
					continue

				# Fetch and write file
				try:
					if is_binary:
						file_content = _fetch_binary_from_github(source_path)
						if file_content:
							if not dest_path.exists() or force:
								dest_path.write_bytes(file_content)
								console.print(f'[green]✓[/green] Created [cyan]{dest_name}[/cyan]')
						else:
							console.print(f'[yellow]⚠[/yellow]  Could not fetch [cyan]{dest_name}[/cyan] from GitHub')
					else:
						file_content = _get_template_content(source_path)
						if _write_init_file(dest_path, file_content, force):
							console.print(f'[green]✓[/green] Created [cyan]{dest_name}[/cyan]')
							# Make executable if needed
							if is_executable and sys.platform != 'win32':
								dest_path.chmod(dest_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
				except Exception as e:
					console.print(f'[yellow]⚠[/yellow]  Error generating [cyan]{dest_name}[/cyan]: {e}')

		# Create a nice panel for next steps
		next_steps = Text()

		# Display next steps from manifest if available
		if 'next_steps' in INIT_TEMPLATES[template]:
			steps = INIT_TEMPLATES[template]['next_steps']
			for i, step in enumerate(steps, 1):
				# Handle footer separately (no numbering)
				if 'footer' in step:
					next_steps.append(f'{step["footer"]}\n', style='dim italic')
					continue

				# Step title
				next_steps.append(f'\n{i}. {step["title"]}:\n', style='bold')

				# Step commands
				for cmd in step.get('commands', []):
					# Replace placeholders
					cmd = cmd.replace('{template}', template)
					cmd = cmd.replace('{output}', output_path.name)
					next_steps.append(f'   {cmd}\n', style='dim')

				# Optional note
				if 'note' in step:
					next_steps.append(f'   {step["note"]}\n', style='dim italic')

				next_steps.append('\n')
		else:
			# Default workflow for templates without custom next_steps
			next_steps.append('\n1. Navigate to project directory:\n', style='bold')
			next_steps.append(f'   cd {template}\n\n', style='dim')
			next_steps.append('2. Initialize uv project:\n', style='bold')
			next_steps.append('   uv init\n\n', style='dim')
			next_steps.append('3. Install browser-use:\n', style='bold')
			next_steps.append('   uv add browser-use\n\n', style='dim')
			next_steps.append('4. Set up your API key in .env file or environment:\n', style='bold')
			next_steps.append('   BROWSER_USE_API_KEY=your-key\n', style='dim')
			next_steps.append(
				'   (Get your key at https://cloud.browser-use.com/dashboard/settings?tab=api-keys&new&utm_source=oss&utm_medium=cli)\n\n',
				style='dim italic',
			)
			next_steps.append('5. Run your script:\n', style='bold')
			next_steps.append(f'   uv run {output_path.name}\n', style='dim')

		console.print(
			Panel(
				next_steps,
				title='[bold]Next steps[/bold]',
				border_style='#fe750e',
				padding=(1, 2),
			)
		)