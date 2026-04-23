def describe(self) -> str:
		"""List all files with their content information using file-specific display methods"""
		DISPLAY_CHARS = 400
		description = ''

		for file_obj in self.files.values():
			# Skip todo.md from description
			if file_obj.full_name == 'todo.md':
				continue

			content = file_obj.read()

			# Handle empty files
			if not content:
				description += f'<file>\n{file_obj.full_name} - [empty file]\n</file>\n'
				continue

			lines = content.splitlines()
			line_count = len(lines)

			# For small files, display the entire content
			whole_file_description = (
				f'<file>\n{file_obj.full_name} - {line_count} lines\n<content>\n{content}\n</content>\n</file>\n'
			)
			if len(content) < int(1.5 * DISPLAY_CHARS):
				description += whole_file_description
				continue

			# For larger files, display start and end previews
			half_display_chars = DISPLAY_CHARS // 2

			# Get start preview
			start_preview = ''
			start_line_count = 0
			chars_count = 0
			for line in lines:
				if chars_count + len(line) + 1 > half_display_chars:
					break
				start_preview += line + '\n'
				chars_count += len(line) + 1
				start_line_count += 1

			# Get end preview
			end_preview = ''
			end_line_count = 0
			chars_count = 0
			for line in reversed(lines):
				if chars_count + len(line) + 1 > half_display_chars:
					break
				end_preview = line + '\n' + end_preview
				chars_count += len(line) + 1
				end_line_count += 1

			# Calculate lines in between
			middle_line_count = line_count - start_line_count - end_line_count
			if middle_line_count <= 0:
				description += whole_file_description
				continue

			start_preview = start_preview.strip('\n').rstrip()
			end_preview = end_preview.strip('\n').rstrip()

			# Format output
			if not (start_preview or end_preview):
				description += f'<file>\n{file_obj.full_name} - {line_count} lines\n<content>\n{middle_line_count} lines...\n</content>\n</file>\n'
			else:
				description += f'<file>\n{file_obj.full_name} - {line_count} lines\n<content>\n{start_preview}\n'
				description += f'... {middle_line_count} more lines ...\n'
				description += f'{end_preview}\n'
				description += '</content>\n</file>\n'

		return description.strip('\n')