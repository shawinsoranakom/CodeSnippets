def __delitem__(self, key):
        "Delete a variable from the current context"
        del self.dicts[-1][key]