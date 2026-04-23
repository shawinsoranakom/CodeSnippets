def search(
        self,
        query: Optional[str] = None,
        tag: Optional[str] = None,
        author: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search catalog for presets.

        Searches across all active catalogs (merged by priority) so that
        community and custom catalogs are included in results.

        Args:
            query: Search query (searches name, description, tags)
            tag: Filter by specific tag
            author: Filter by author name

        Returns:
            List of matching preset metadata
        """
        try:
            packs = self._get_merged_packs()
        except PresetError:
            return []

        results = []

        for pack_id, pack_data in packs.items():
            if author and pack_data.get("author", "").lower() != author.lower():
                continue

            if tag and tag.lower() not in [
                t.lower() for t in pack_data.get("tags", [])
            ]:
                continue

            if query:
                query_lower = query.lower()
                searchable_text = " ".join(
                    [
                        pack_data.get("name", ""),
                        pack_data.get("description", ""),
                        pack_id,
                    ]
                    + pack_data.get("tags", [])
                ).lower()

                if query_lower not in searchable_text:
                    continue

            results.append({**pack_data, "id": pack_id})

        return results