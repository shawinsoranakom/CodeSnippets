def __str__(self):
        if hasattr(self, "error_dict"):
            return repr(dict(self))
        return repr(list(self))