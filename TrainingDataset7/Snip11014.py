def _check_null_allowed_for_primary_keys(self):
        if (
            self.primary_key
            and self.null
            and not connection.features.interprets_empty_strings_as_nulls
        ):
            # We cannot reliably check this for backends like Oracle which
            # consider NULL and '' to be equal (and thus set up
            # character-based fields a little differently).
            return [
                checks.Error(
                    "Primary keys must not have null=True.",
                    hint=(
                        "Set null=False on the field, or "
                        "remove primary_key=True argument."
                    ),
                    obj=self,
                    id="fields.E007",
                )
            ]
        else:
            return []