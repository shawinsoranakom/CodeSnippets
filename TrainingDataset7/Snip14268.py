def appendlist(self, key, value):
        """Append an item to the internal list associated with key."""
        self.setlistdefault(key).append(value)