def _set_next_sequence(self):
        """Set the next sequence.

        This method ensures that the field is set both in the ORM and in the database.
        This is necessary because we use a database query to get the previous sequence,
        and we need that query to always be executed on the latest data.
        """
        self.ensure_one()
        format_string, format_values = self._get_next_sequence_format()

        sequence = self._locked_increment(format_string, format_values)
        self.with_context(clear_sequence_mixin_cache=False)[self._sequence_field] = sequence

        registry = self.env.registry
        triggers = registry._field_triggers[self._fields[self._sequence_field]]
        for inverse_field, triggered_fields in triggers.items():
            for triggered_field in triggered_fields:
                if not triggered_field.store or not triggered_field.compute:
                    continue
                for field in registry.field_inverses[inverse_field[0]] if inverse_field else [None]:
                    self.env.add_to_compute(triggered_field, self[field.name] if field else self)

        self._compute_split_sequence()