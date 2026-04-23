async def replace_file_str(self, full_filename: str, old_str: str, new_str: str) -> str:
		"""Replace old_str with new_str in file_name"""
		original_filename = full_filename
		resolved, was_sanitized = self._resolve_filename(full_filename)
		if not self._is_valid_filename(resolved):
			return _build_filename_error_message(full_filename, self.get_allowed_extensions())
		full_filename = resolved

		if not old_str:
			return 'Error: Cannot replace empty string. Please provide a non-empty string to replace.'

		file_obj = self.files.get(full_filename)
		if not file_obj:
			if was_sanitized:
				return f"File '{full_filename}' not found. (Filename was auto-corrected from '{original_filename}')"
			return f"File '{full_filename}' not found."

		try:
			content = file_obj.read()
			content = content.replace(old_str, new_str)
			await file_obj.write(content, self.data_dir)
			sanitize_note = f" (auto-corrected from '{original_filename}')" if was_sanitized else ''
			return f'Successfully replaced all occurrences of "{old_str}" with "{new_str}" in file {full_filename}{sanitize_note}'
		except FileSystemError as e:
			return str(e)
		except Exception as e:
			return f"Error: Could not replace string in file '{full_filename}'. {str(e)}"