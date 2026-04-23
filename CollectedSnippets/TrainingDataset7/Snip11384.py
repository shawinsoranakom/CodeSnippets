def _check_related_query_name_is_valid(self):
        if self.remote_field.hidden:
            return []
        rel_query_name = self.related_query_name()
        errors = []
        if rel_query_name.endswith("_"):
            errors.append(
                checks.Error(
                    "Reverse query name '%s' must not end with an underscore."
                    % rel_query_name,
                    hint=(
                        "Add or change a related_name or related_query_name "
                        "argument for this field."
                    ),
                    obj=self,
                    id="fields.E308",
                )
            )
        if LOOKUP_SEP in rel_query_name:
            errors.append(
                checks.Error(
                    "Reverse query name '%s' must not contain '%s'."
                    % (rel_query_name, LOOKUP_SEP),
                    hint=(
                        "Add or change a related_name or related_query_name "
                        "argument for this field."
                    ),
                    obj=self,
                    id="fields.E309",
                )
            )
        return errors