def add(self, records, fields=None, extra_fields=None, as_thread=False, **kwargs):
        """Add records to the store. Data is coming from _to_store() method of the model if it is
        defined, and fallbacks to _read_format() otherwise.
        Relations are defined with Store.One() or Store.Many() instead of a field name as string.

        Use case: to add records and their fields to store. This is the preferred method.
        """
        if not records:
            return self
        assert isinstance(records, models.Model)
        if fields is None:
            if as_thread:
                fields = []
            else:
                fields = (
                    records._to_store_defaults(self.target)
                    if hasattr(records, "_to_store_defaults")
                    else []
                )
        fields = self._format_fields(records, fields) + self._format_fields(records, extra_fields)
        if as_thread:
            if hasattr(records, "_thread_to_store"):
                records._thread_to_store(self, fields, **kwargs)
            else:
                assert not kwargs
                self.add_records_fields(records, fields, as_thread=True)
        else:
            if hasattr(records, "_to_store"):
                records._to_store(self, fields, **kwargs)
            else:
                assert not kwargs
                self.add_records_fields(records, fields)
        return self