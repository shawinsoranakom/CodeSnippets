def _update_cache(self, values: ValuesType, validate: bool = True) -> None:
        """ Update the cache of ``self`` with ``values``.

            :param values: dict of field values, in any format.
            :param validate: whether values must be checked
        """
        self.ensure_one()
        fields = self._fields
        try:
            field_values = [(fields[name], value) for name, value in values.items() if name != 'id']
        except KeyError as e:
            raise ValueError("Invalid field %r on model %r" % (e.args[0], self._name))

        # convert monetary fields after other columns for correct value rounding
        for field, value in sorted(field_values, key=lambda item: item[0].write_sequence):
            value = field.convert_to_cache(value, self, validate)
            field._update_cache(self, value)

            # set inverse fields on new records in the comodel
            if field.relational:
                inv_recs = self[field.name].filtered(lambda r: not r.id)
                if not inv_recs:
                    continue
                # we need to adapt the value of the inverse fields to integrate self into it:
                # x2many fields should add self, while many2one fields should replace with self
                for invf in self.pool.field_inverses[field]:
                    invf._update_inverse(inv_recs, self)