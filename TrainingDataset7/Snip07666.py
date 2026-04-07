def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if path == "django.contrib.postgres.fields.array.ArrayField":
            path = "django.contrib.postgres.fields.ArrayField"
        kwargs["base_field"] = self.base_field.clone()
        if self.size is not None:
            kwargs["size"] = self.size
        return name, path, args, kwargs