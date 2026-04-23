def _build_content(self, entry: Any, semantic_identifier: str) -> str:
        parts = [semantic_identifier]
        content_blocks = entry.get("content") or []

        for block in content_blocks:
            value = block.get("value") if isinstance(block, dict) else None
            normalized = self._normalize_text(value)
            if normalized:
                parts.append(normalized)

        if len(parts) == 1:
            fallback = entry.get("summary") or entry.get("description") or ""
            normalized = self._normalize_text(fallback)
            if normalized:
                parts.append(normalized)

        return "\n\n".join(part for part in parts if part).strip()