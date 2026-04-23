def search(
        self,
        query: Optional[str] = None,
        tag: Optional[str] = None,
        author: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search catalogs for integrations matching the given filters."""
        results: List[Dict[str, Any]] = []
        for item in self._get_merged_integrations():
            author_val = item.get("author", "")
            if not isinstance(author_val, str):
                author_val = str(author_val) if author_val is not None else ""
            if author and author_val.lower() != author.lower():
                continue
            if tag:
                raw_tags = item.get("tags", [])
                tags_list = raw_tags if isinstance(raw_tags, list) else []
                if tag.lower() not in [t.lower() for t in tags_list if isinstance(t, str)]:
                    continue
            if query:
                raw_tags = item.get("tags", [])
                tags_list = raw_tags if isinstance(raw_tags, list) else []
                name_val = item.get("name", "")
                desc_val = item.get("description", "")
                id_val = item.get("id", "")
                haystack = " ".join(
                    [
                        str(name_val) if name_val else "",
                        str(desc_val) if desc_val else "",
                        str(id_val) if id_val else "",
                    ]
                    + [t for t in tags_list if isinstance(t, str)]
                ).lower()
                if query.lower() not in haystack:
                    continue
            results.append(item)
        return results