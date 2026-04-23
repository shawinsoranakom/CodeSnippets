def contribute_to_class(self, *args, **kwargs):
        super().contribute_to_class(*args, **kwargs)

        self._query = Query(model=self.model, alias_cols=False)
        # Register lookups from the output_field class.
        for lookup_name, lookup in self.output_field.get_class_lookups().items():
            self.register_lookup(lookup, lookup_name=lookup_name)