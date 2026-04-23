def _build_attachment_content(self, artifacts: list, artifact_urls: list[dict] | None = None) -> str:
        sections = []
        artifact_urls = artifact_urls or []

        for idx, art in enumerate(artifacts, start=1):
            key = f"attachment{idx}"
            try:
                name = _art_field(art, "name")
                content_b64 = _art_field(art, "content_b64")
                mime_type = _art_field(art, "mime_type")
                if not name or not content_b64:
                    continue

                blob = base64.b64decode(content_b64)
                parsed = FileService.parse(
                    name,
                    blob,
                    False,
                    tenant_id=self._canvas.get_tenant_id(),
                )
                attachment_type = self._normalize_attachment_type(name, mime_type)
                section = self._format_attachment_section(key, attachment_type, name, parsed)
                sections.append(section)
                logging.info(f"[CodeExec]: parse attachment section key='{key}' from artifact='{name}'")
            except Exception as e:
                logging.warning(f"[CodeExec]: Failed to parse artifact for content section '{key}': {e}")
                fallback_type = self._normalize_attachment_type(name, mime_type)
                fallback_name = name
                fallback_url = ""
                if idx - 1 < len(artifact_urls):
                    fallback_url = artifact_urls[idx - 1].get("url", "")
                fallback_text = "Artifact generated but parse failed."
                if fallback_url:
                    fallback_text += f" Download: {fallback_url}"
                sections.append(self._format_attachment_section(key, fallback_type, fallback_name, fallback_text))

        if sections:
            return f"attachment_count: {len(sections)}\n\n" + "\n\n".join(sections)
        return "attachment_count: 0"