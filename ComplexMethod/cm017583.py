def _check_fieldsets_item(self, obj, fieldset, label, seen_fields):
        """Check an item of `fieldsets`, i.e. check that this is a pair of a
        set name and a dictionary containing "fields" key."""

        if not isinstance(fieldset, (list, tuple)):
            return must_be("a list or tuple", option=label, obj=obj, id="admin.E008")
        elif len(fieldset) != 2:
            return must_be("of length 2", option=label, obj=obj, id="admin.E009")
        elif not isinstance(fieldset[1], dict):
            return must_be(
                "a dictionary", option="%s[1]" % label, obj=obj, id="admin.E010"
            )
        elif "fields" not in fieldset[1]:
            return [
                checks.Error(
                    "The value of '%s[1]' must contain the key 'fields'." % label,
                    obj=obj.__class__,
                    id="admin.E011",
                )
            ]
        elif not isinstance(fieldset[1]["fields"], (list, tuple)):
            return must_be(
                "a list or tuple",
                option="%s[1]['fields']" % label,
                obj=obj,
                id="admin.E008",
            )

        fieldset_fields = flatten(fieldset[1]["fields"])
        seen_fields.extend(fieldset_fields)
        field_counts = collections.Counter(seen_fields)
        fieldset_fields_set = set(fieldset_fields)
        if duplicate_fields := [
            field
            for field, count in field_counts.items()
            if count > 1 and field in fieldset_fields_set
        ]:
            return [
                checks.Error(
                    "There are duplicate field(s) in '%s[1]'." % label,
                    hint="Remove duplicates of %s."
                    % ", ".join(map(repr, duplicate_fields)),
                    obj=obj.__class__,
                    id="admin.E012",
                )
            ]
        return list(
            chain.from_iterable(
                self._check_field_spec(obj, fieldset_fields, '%s[1]["fields"]' % label)
                for fieldset_fields in fieldset[1]["fields"]
            )
        )