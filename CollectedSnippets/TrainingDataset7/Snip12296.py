def clear_deferred_loading(self):
        """Remove any fields from the deferred loading set."""
        self.deferred_loading = (frozenset(), True)