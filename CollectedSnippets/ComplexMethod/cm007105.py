def _save_dataframe(self, dataframe: DataFrame, path: Path, fmt: str) -> str:
        """Save a DataFrame to the specified file format."""
        append_mode = getattr(self, "append_mode", False)
        should_append = append_mode and path.exists() and self._is_plain_text_format(fmt)

        if fmt == "csv":
            dataframe.to_csv(path, index=False, mode="a" if should_append else "w", header=not should_append)
        elif fmt == "excel":
            dataframe.to_excel(path, index=False, engine="openpyxl")
        elif fmt == "json":
            if should_append:
                # Read and parse existing JSON
                existing_data = []
                try:
                    existing_content = path.read_text(encoding="utf-8").strip()
                    if existing_content:
                        parsed = json.loads(existing_content)
                        # Handle case where existing content is a single object
                        if isinstance(parsed, dict):
                            existing_data = [parsed]
                        elif isinstance(parsed, list):
                            existing_data = parsed
                except (json.JSONDecodeError, FileNotFoundError):
                    # Treat parse errors or missing file as empty array
                    existing_data = []

                # Append new data
                new_records = json.loads(dataframe.to_json(orient="records"))
                existing_data.extend(new_records)

                # Write back as a single JSON array
                path.write_text(json.dumps(existing_data, indent=2), encoding="utf-8")
            else:
                dataframe.to_json(path, orient="records", indent=2)
        elif fmt == "markdown":
            content = dataframe.to_markdown(index=False)
            if should_append:
                path.write_text(path.read_text(encoding="utf-8") + "\n\n" + content, encoding="utf-8")
            else:
                path.write_text(content, encoding="utf-8")
        else:
            msg = f"Unsupported DataFrame format: {fmt}"
            raise ValueError(msg)
        action = "appended to" if should_append else "saved successfully as"
        return f"DataFrame {action} '{path}'"