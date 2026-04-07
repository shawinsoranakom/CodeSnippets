def deconstruct(self):
        path = "%s.%s" % (self.__class__.__module__, self.__class__.__name__)
        path = path.replace("django.db.models.indexes", "django.db.models")
        kwargs = {"name": self.name}
        if self.fields:
            kwargs["fields"] = self.fields
        if self.db_tablespace is not None:
            kwargs["db_tablespace"] = self.db_tablespace
        if self.opclasses:
            kwargs["opclasses"] = self.opclasses
        if self.condition:
            kwargs["condition"] = self.condition
        if self.include:
            kwargs["include"] = self.include
        return (path, self.expressions, kwargs)