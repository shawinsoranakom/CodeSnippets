def _check_field_spec(self, obj, fields, label):
        """`fields` should be an item of `fields` or an item of
        fieldset[1]['fields'] for any `fieldset` in `fieldsets`. It should be a
        field name or a tuple of field names."""

        if isinstance(fields, tuple):
            return list(
                chain.from_iterable(
                    self._check_field_spec_item(
                        obj, field_name, "%s[%d]" % (label, index)
                    )
                    for index, field_name in enumerate(fields)
                )
            )
        else:
            return self._check_field_spec_item(obj, fields, label)