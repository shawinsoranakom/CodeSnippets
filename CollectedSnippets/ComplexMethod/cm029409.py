async def read_file(file_name: str, available_file_paths: list[str], file_system: FileSystem):
			if available_file_paths and file_name in available_file_paths:
				structured_result = await file_system.read_file_structured(file_name, external_file=True)
			else:
				structured_result = await file_system.read_file_structured(file_name)

			result = structured_result['message']
			images = structured_result.get('images')

			MAX_MEMORY_SIZE = 1000
			# For images, create a shorter memory message
			if images:
				memory = f'Read image file {file_name}'
			elif len(result) > MAX_MEMORY_SIZE:
				lines = result.splitlines()
				display = ''
				lines_count = 0
				for line in lines:
					if len(display) + len(line) < MAX_MEMORY_SIZE:
						display += line + '\n'
						lines_count += 1
					else:
						break
				remaining_lines = len(lines) - lines_count
				memory = f'{display}{remaining_lines} more lines...' if remaining_lines > 0 else display
			else:
				memory = result
			logger.info(f'💾 {memory}')
			return ActionResult(
				extracted_content=result,
				long_term_memory=memory,
				images=images,
				include_extracted_content_only_once=True,
			)