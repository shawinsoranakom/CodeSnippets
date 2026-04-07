def value_from_object(self, obj):
        return list(getattr(obj, self.attname).all()) if obj._is_pk_set() else []