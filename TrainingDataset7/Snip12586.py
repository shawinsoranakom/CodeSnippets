def __getitem__(self, index):
        """Return the form at the given index, based on the rendering order."""
        return self.forms[index]