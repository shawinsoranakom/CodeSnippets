def _read_excels(self):
        """Read and parse Excel files into structured data."""
        all_data = {}
        summaries = []
        markdown_parts = []

        for file_ref in (self._param.input_files or []):
            if self.check_if_canceled("ExcelProcessor reading"):
                return

            # Get variable value
            value = self._canvas.get_variable_value(file_ref)
            self.set_input_value(file_ref, str(value)[:200] if value else "")

            if value is None:
                continue

            # Handle file content
            content, filename = self._get_file_content(file_ref)
            if content is None:
                continue

            # Parse Excel
            dfs = self._parse_excel_to_dataframes(content, filename)

            for sheet_name, df in dfs.items():
                key = f"{filename}_{sheet_name}" if len(dfs) > 1 else filename
                all_data[key] = df.to_dict(orient="records")

                # Build summary
                summaries.append(f"**{key}**: {len(df)} rows, {len(df.columns)} columns ({', '.join(df.columns.tolist()[:5])}{'...' if len(df.columns) > 5 else ''})")

                # Build markdown table
                markdown_parts.append(f"### {key}\n\n{df.head(10).to_markdown(index=False)}\n")

        # Set outputs
        self.set_output("data", all_data)
        self.set_output("summary", "\n".join(summaries) if summaries else "No Excel files found")
        self.set_output("markdown", "\n\n".join(markdown_parts) if markdown_parts else "No data")