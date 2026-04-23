def relations(self):
        if self._relations is None:
            self.resolve_fields_and_relations()
        return self._relations