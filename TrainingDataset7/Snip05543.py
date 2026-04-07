def _check_fieldsets(self, obj):
        """Check that fieldsets is properly formatted and doesn't contain
        duplicates."""

        if obj.fieldsets is None:
            return []
        elif not isinstance(obj.fieldsets, (list, tuple)):
            return must_be(
                "a list or tuple", option="fieldsets", obj=obj, id="admin.E007"
            )
        else:
            seen_fields = []
            return list(
                chain.from_iterable(
                    self._check_fieldsets_item(
                        obj, fieldset, "fieldsets[%d]" % index, seen_fields
                    )
                    for index, fieldset in enumerate(obj.fieldsets)
                )
            )