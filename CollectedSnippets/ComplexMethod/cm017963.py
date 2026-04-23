def _convert(self, notebook_content: dict) -> DocumentConverterResult:
        """Helper function that converts notebook JSON content to Markdown."""
        try:
            md_output = []
            title = None

            for cell in notebook_content.get("cells", []):
                cell_type = cell.get("cell_type", "")
                source_lines = cell.get("source", [])

                if cell_type == "markdown":
                    md_output.append("".join(source_lines))

                    # Extract the first # heading as title if not already found
                    if title is None:
                        for line in source_lines:
                            if line.startswith("# "):
                                title = line.lstrip("# ").strip()
                                break

                elif cell_type == "code":
                    # Code cells are wrapped in Markdown code blocks
                    md_output.append(f"```python\n{''.join(source_lines)}\n```")
                elif cell_type == "raw":
                    md_output.append(f"```\n{''.join(source_lines)}\n```")

            md_text = "\n\n".join(md_output)

            # Check for title in notebook metadata
            title = notebook_content.get("metadata", {}).get("title", title)

            return DocumentConverterResult(
                markdown=md_text,
                title=title,
            )

        except Exception as e:
            raise FileConversionException(
                f"Error converting .ipynb file: {str(e)}"
            ) from e