def ref_alias(self, alias):
        """Increases the reference count for this alias."""
        self.alias_refcount[alias] += 1