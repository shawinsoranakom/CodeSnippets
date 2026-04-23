async def process_file_async(self, file_path):
        try:
            file_content = await self.aread_file_content(file_path)
        except Exception:  # noqa: BLE001
            await logger.aexception(f"Error while reading file {file_path}")
            return False, f"Could not read {file_path}"

        if file_content is None:
            return False, f"Could not read {file_path}"
        if self.is_empty_file(file_content):
            return False, "Empty file"
        if not self.validate_code(file_content):
            return False, "Syntax error"
        if self._is_type_hint_used_in_args("Optional", file_content) and not self._is_type_hint_imported(
            "Optional", file_content
        ):
            return (
                False,
                "Type hint 'Optional' is used but not imported in the code.",
            )
        if self.compress_code_field:
            file_content = str(StringCompressor(file_content).compress_string())
        return True, file_content