def __get__(self, instance, cls=None):
        """
        Retrieve and caches the value from the datastore on the first lookup.
        Return the cached value.
        """
        if instance is None:
            return self
        data = instance.__dict__
        field_name = self.field.attname
        if field_name not in data:
            # Let's see if the field is part of the parent chain. If so we
            # might be able to reuse the already loaded value. Refs #18343.
            val = self._check_parent_chain(instance)
            if val is None:
                if not instance._is_pk_set():
                    raise AttributeError(
                        f"Cannot retrieve deferred field {field_name!r} "
                        "from an unsaved model."
                    )

                instance._state.fetch_mode.fetch(self, instance)
            else:
                data[field_name] = val
        return data[field_name]