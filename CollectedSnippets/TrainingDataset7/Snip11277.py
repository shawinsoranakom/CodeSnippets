def __getstate__(self):
        # FieldFile needs access to its associated model field, an instance and
        # the file's name. Everything else will be restored later, by
        # FileDescriptor below.
        return {
            "name": self.name,
            "closed": False,
            "_committed": True,
            "_file": None,
            "instance": self.instance,
            "field": self.field,
        }