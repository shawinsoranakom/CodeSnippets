def refresh_from_db(self, using=None, fields=None, **kwargs):
        # Reloads all deferred fields if any of the fields is deferred.
        if fields is not None:
            fields = set(fields)
            deferred_fields = self.get_deferred_fields()
            if fields.intersection(deferred_fields):
                fields = fields.union(deferred_fields)
        super().refresh_from_db(using, fields, **kwargs)