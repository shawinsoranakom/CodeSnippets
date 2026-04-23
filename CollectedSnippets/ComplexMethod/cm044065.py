def validate_model(cls, values) -> "PdfResponseModel":
        """Validate the PDF content."""
        # pylint: disable=import-outside-toplevel
        import base64  # noqa
        from io import BytesIO

        content = getattr(values, "content", None)
        file_reference = getattr(values, "url", None)
        filename = getattr(values, "filename", "")

        if not content and not file_reference:
            raise ValueError("Either 'content' or 'url' must be provided.")

        if file_reference and "://" not in file_reference:
            raise ValueError("Invalid URL reference provided")

        if content:
            pdf = (
                base64.b64encode(BytesIO(content).getvalue()).decode("utf-8")
                if isinstance(content, bytes)
                else content
            )

        values.content = pdf
        if file_reference:
            values.url = file_reference
        elif hasattr(values, "url"):
            del values.url
        values.data_format = {"data_type": "pdf", "filename": filename}

        return values