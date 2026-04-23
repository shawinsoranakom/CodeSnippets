def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if kwargs.get("max_length") == 50:
            del kwargs["max_length"]
        if self.db_index is False:
            kwargs["db_index"] = False
        else:
            del kwargs["db_index"]
        if self.allow_unicode is not False:
            kwargs["allow_unicode"] = self.allow_unicode
        return name, path, args, kwargs