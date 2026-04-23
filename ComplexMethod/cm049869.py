def _track_get_fields(self):
        """ Return the set of tracked fields names for the current model. """
        model_fields = {
            name
            for name, field in self._fields.items()
            if getattr(field, 'tracking', None)
        }
        # track the properties changes ONLY if the parent changed
        model_fields |= {
            fname for fname, f in self._fields.items()
            if f.type == "properties"
            and f.definition_record in model_fields
            and getattr(f, "tracking", None) is not False
        }

        return model_fields and set(self.fields_get(model_fields, attributes=()))