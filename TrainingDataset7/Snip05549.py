def _check_filter_vertical(self, obj):
        """Check that filter_vertical is a sequence of field names."""
        if not isinstance(obj.filter_vertical, (list, tuple)):
            return must_be(
                "a list or tuple", option="filter_vertical", obj=obj, id="admin.E017"
            )
        else:
            return list(
                chain.from_iterable(
                    self._check_filter_item(
                        obj, field_name, "filter_vertical[%d]" % index
                    )
                    for index, field_name in enumerate(obj.filter_vertical)
                )
            )