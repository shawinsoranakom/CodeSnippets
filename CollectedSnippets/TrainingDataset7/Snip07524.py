def start_object(self, obj):
        super().start_object(obj)
        self._geometry = None
        if self.geometry_field is None:
            # Find the first declared geometry field
            for field in obj._meta.fields:
                if hasattr(field, "geom_type"):
                    self.geometry_field = field.name
                    break