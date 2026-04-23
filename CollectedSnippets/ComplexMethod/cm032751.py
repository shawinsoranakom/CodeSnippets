def _check_payloads(self) -> "TokenizerFromUpstream":
        # Empty chunk arrays are valid upstream results for nearly empty files.
        if self.output_format == "chunks" and self.chunks is not None:
            return self

        if self.output_format in {"markdown", "text", "html"}:
            if self.output_format == "markdown" and self.markdown_result is None:
                raise ValueError("output_format=markdown requires a markdown payload (field: 'markdown' or 'markdown_result').")
            if self.output_format == "text" and self.text_result is None:
                raise ValueError("output_format=text requires a text payload (field: 'text' or 'text_result').")
            if self.output_format == "html" and self.html_result is None:
                raise ValueError("output_format=text requires a html payload (field: 'html' or 'html_result').")
        else:
            # Distinguish a missing JSON payload from a present-but-empty one.
            if self.json_result is None and self.chunks is None:
                raise ValueError("When no chunks are provided and output_format is not markdown/text, a JSON list payload is required (field: 'json' or 'json_result').")
        return self