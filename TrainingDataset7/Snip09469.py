def references_index(self, table, index):
        return any(
            hasattr(part, "references_index") and part.references_index(table, index)
            for part in self.parts.values()
        )