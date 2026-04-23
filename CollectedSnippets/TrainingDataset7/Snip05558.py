def _check_prepopulated_fields_value(self, obj, val, label):
        """Check a value of `prepopulated_fields` dictionary, i.e. it's an
        iterable of existing fields."""

        if not isinstance(val, (list, tuple)):
            return must_be("a list or tuple", option=label, obj=obj, id="admin.E029")
        else:
            return list(
                chain.from_iterable(
                    self._check_prepopulated_fields_value_item(
                        obj, subfield_name, "%s[%r]" % (label, index)
                    )
                    for index, subfield_name in enumerate(val)
                )
            )