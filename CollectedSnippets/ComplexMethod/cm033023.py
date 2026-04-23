def _build_page_path(self, page: NotionPage, visited: Optional[set[str]] = None) -> Optional[str]:
        """Construct a hierarchical path for a page based on its parent chain."""
        if page.id in self.page_path_cache:
            return self.page_path_cache[page.id]

        visited = visited or set()
        if page.id in visited:
            logging.warning(f"[Notion]: Detected cycle while building path for page {page.id}")
            return self._read_page_title(page)
        visited.add(page.id)

        current_title = self._read_page_title(page) or f"Untitled Page {page.id}"

        parent_info = getattr(page, "parent", None) or {}
        parent_type = parent_info.get("type")
        parent_id = parent_info.get(parent_type) if parent_type else None

        parent_path = None
        if parent_type in {"page_id", "database_id"} and isinstance(parent_id, str):
            try:
                parent_page = self._fetch_page(parent_id)
                parent_path = self._build_page_path(parent_page, visited)
            except Exception as exc:
                logging.warning(f"[Notion]: Failed to resolve parent {parent_id} for page {page.id}: {exc}")

        full_path = f"{parent_path} / {current_title}" if parent_path else current_title
        self.page_path_cache[page.id] = full_path
        return full_path