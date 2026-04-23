def search(
        self,
        query: str | None = None,
        tag: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search workflows across all configured catalogs."""
        merged = self._get_merged_workflows()
        results: list[dict[str, Any]] = []

        for wf_id, wf_data in merged.items():
            wf_data.setdefault("id", wf_id)
            if query:
                q = query.lower()
                searchable = " ".join(
                    [
                        wf_data.get("name", ""),
                        wf_data.get("description", ""),
                        wf_data.get("id", ""),
                    ]
                ).lower()
                if q not in searchable:
                    continue
            if tag:
                raw_tags = wf_data.get("tags", [])
                tags = raw_tags if isinstance(raw_tags, list) else []
                normalized_tags = [t.lower() for t in tags if isinstance(t, str)]
                if tag.lower() not in normalized_tags:
                    continue
            results.append(wf_data)
        return results