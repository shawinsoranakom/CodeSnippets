def validate_and_display_output(output: str, schema_model: type[BaseModel]):
	"""
	Validate the JSON output against the schema and display results.

	Args:
	    output: Raw JSON string from the task
	    schema_model: Pydantic model for validation
	"""
	print('\n📊 Structured Output Analysis')
	print('=' * 40)

	try:
		# Parse and validate the JSON
		parsed_data = schema_model.model_validate_json(output)
		print('✅ JSON validation successful!')

		# Pretty print the structured data
		print('\n📋 Parsed Data:')
		print('-' * 20)
		print(parsed_data.model_dump_json(indent=2))

		# Display specific fields based on model type
		if isinstance(parsed_data, NewsResponse):
			print(f'\n📰 Found {len(parsed_data.articles)} articles from {parsed_data.source_website}')
			for i, article in enumerate(parsed_data.articles[:3], 1):
				print(f'\n{i}. {article.title}')
				print(f'   Summary: {article.summary[:100]}...')
				print(f'   URL: {article.url}')

		elif isinstance(parsed_data, ProductInfo):
			print(f'\n🛍️  Product: {parsed_data.name}')
			print(f'   Price: ${parsed_data.price}')
			print(f'   Rating: {parsed_data.rating}/5' if parsed_data.rating else '   Rating: N/A')
			print(f'   Status: {parsed_data.availability}')

		elif isinstance(parsed_data, CompanyInfo):
			print(f'\n🏢 Company: {parsed_data.name}')
			print(f'   Industry: {parsed_data.industry}')
			print(f'   Headquarters: {parsed_data.headquarters}')
			if parsed_data.founded_year:
				print(f'   Founded: {parsed_data.founded_year}')

		return parsed_data

	except ValidationError as e:
		print('❌ JSON validation failed!')
		print(f'Errors: {e}')
		print(f'\nRaw output: {output[:500]}...')
		return None

	except json.JSONDecodeError as e:
		print('❌ Invalid JSON format!')
		print(f'Error: {e}')
		print(f'\nRaw output: {output[:500]}...')
		return None