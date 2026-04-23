def _extract_file_metadata(self, result_obj: dict[str, Any], block_id: str) -> tuple[str | None, str, str | None]:
        file_source_type = result_obj.get("type")
        file_source = result_obj.get(file_source_type, {}) if file_source_type else {}
        url = file_source.get("url")

        name = result_obj.get("name") or file_source.get("name")
        if url and not name:
            parsed_name = Path(urlparse(url).path).name
            name = parsed_name or f"notion_file_{block_id}"
        elif not name:
            name = f"notion_file_{block_id}"

        name = self._append_block_id_to_name(name, block_id)

        caption = self._extract_rich_text(result_obj.get("caption", [])) if "caption" in result_obj else None

        return url, name, caption