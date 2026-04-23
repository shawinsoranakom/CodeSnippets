def _stringify_message_value(
        self,
        value: Any,
        delimiter: str = None,
        downloads: list[dict[str, Any]] | None = None,
        fallback_to_str: bool = False,
    ) -> str:
        extracted_downloads = self._extract_downloads(value)
        if extracted_downloads:
            if downloads is not None:
                downloads.extend(extracted_downloads)
            return ""

        if value is None:
            return ""

        if isinstance(value, list) and delimiter:
            return delimiter.join([str(vv) for vv in value])

        if isinstance(value, str):
            return value

        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            if fallback_to_str:
                return str(value)
            return ""