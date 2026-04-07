def value_from_object(self, obj):
        """Return the value of this field in the given model instance."""
        return getattr(obj, self.attname)