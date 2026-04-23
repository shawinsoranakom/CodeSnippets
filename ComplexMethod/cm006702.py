def smart_column_order(self) -> "DataFrame":
        """Reorder columns: content-like columns first, system metadata last."""
        if self.empty:
            return self

        content_cols = [c for c in self.columns if c.lower() in self._CONTENT_COLUMNS]
        system_cols = [c for c in self.columns if c.lower() in self._SYSTEM_COLUMNS or c.startswith("_")]
        regular_cols = [c for c in self.columns if c not in content_cols and c not in system_cols]

        new_order = content_cols + regular_cols + system_cols
        return self[new_order]