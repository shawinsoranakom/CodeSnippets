def _check_ordering(self, obj):
        """Check that ordering refers to existing fields or is random."""

        # ordering = None
        if obj.ordering is None:  # The default value is None
            return []
        elif not isinstance(obj.ordering, (list, tuple)):
            return must_be(
                "a list or tuple", option="ordering", obj=obj, id="admin.E031"
            )
        else:
            return list(
                chain.from_iterable(
                    self._check_ordering_item(obj, field_name, "ordering[%d]" % index)
                    for index, field_name in enumerate(obj.ordering)
                )
            )