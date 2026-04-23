async def run(
        self, input_data: Input, *, credentials: GoogleCredentials, **kwargs
    ) -> BlockOutput:
        if not input_data.document:
            yield "error", "No document selected"
            return

        validation_error = _validate_document_file(input_data.document)
        if validation_error:
            yield "error", validation_error
            return

        # Determine rows/columns from content if provided
        content = input_data.content

        # Check if content is valid:
        # 1. Has at least one row with at least one cell (even if empty string)
        # 2. Has at least one non-empty cell value
        has_valid_structure = bool(content and any(len(row) > 0 for row in content))
        has_content = has_valid_structure and any(
            cell for row in content for cell in row
        )

        if has_content:
            # Use content dimensions - filter out empty rows for row count,
            # use max column count across all rows
            rows = len(content)
            columns = max(len(row) for row in content)
        else:
            # No valid content - use explicit rows/columns, clear content
            rows = input_data.rows
            columns = input_data.columns
            content = []  # Clear so we skip population step

        try:
            service = _build_docs_service(credentials)
            result = await asyncio.to_thread(
                self._insert_table,
                service,
                input_data.document.id,
                rows,
                columns,
                input_data.index,
                content,
                input_data.format_as_markdown,
            )
            yield "result", result
            yield "document", _make_document_output(input_data.document)
        except Exception as e:
            yield "error", f"Failed to insert table: {str(e)}"