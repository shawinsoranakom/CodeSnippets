def flatten(self):
        """
        Return self.dicts as one dictionary.
        """
        flat = {}
        for d in self.dicts:
            flat.update(d)
        return flat