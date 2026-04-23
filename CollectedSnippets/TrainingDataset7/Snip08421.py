def messages(self):
        if hasattr(self, "error_dict"):
            return sum(dict(self).values(), [])
        return list(self)