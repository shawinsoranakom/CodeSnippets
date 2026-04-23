def unref_alias(self, alias, amount=1):
        """Decreases the reference count for this alias."""
        self.alias_refcount[alias] -= amount