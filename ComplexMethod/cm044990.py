def search(
        self,
        query: Optional[str] = None,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        verified_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Search catalog for extensions across all active catalogs.

        Args:
            query: Search query (searches name, description, tags)
            tag: Filter by specific tag
            author: Filter by author name
            verified_only: If True, show only verified extensions

        Returns:
            List of matching extension metadata, each annotated with
            ``_catalog_name`` and ``_install_allowed`` from its source catalog.
        """
        all_extensions = self._get_merged_extensions()

        results = []

        for ext_data in all_extensions:
            ext_id = ext_data["id"]

            # Apply filters
            if verified_only and not ext_data.get("verified", False):
                continue

            if author and ext_data.get("author", "").lower() != author.lower():
                continue

            if tag and tag.lower() not in [t.lower() for t in ext_data.get("tags", [])]:
                continue

            if query:
                # Search in name, description, and tags
                query_lower = query.lower()
                searchable_text = " ".join(
                    [
                        ext_data.get("name", ""),
                        ext_data.get("description", ""),
                        ext_id,
                    ]
                    + ext_data.get("tags", [])
                ).lower()

                if query_lower not in searchable_text:
                    continue

            results.append(ext_data)

        return results