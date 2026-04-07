def normalize_table_name(self, table_name):
        """Translate the table name to a Python-compatible model name."""
        return re.sub(r"[^a-zA-Z0-9]", "", table_name.title())