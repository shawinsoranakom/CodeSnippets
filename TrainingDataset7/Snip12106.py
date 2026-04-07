def get_lookup(self, lookup_name):
        from django.db.models.lookups import Lookup

        found = self._get_lookup(lookup_name)
        if found is None and hasattr(self, "output_field"):
            return self.output_field.get_lookup(lookup_name)
        if found is not None and not issubclass(found, Lookup):
            return None
        return found