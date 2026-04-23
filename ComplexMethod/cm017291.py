def references_field(self, model_name, name, app_label):
        model_name_lower = model_name.lower()
        # Check if this operation locally references the field.
        if model_name_lower == self.model_name_lower:
            if name == self.name:
                return True
            if self.field:
                if (
                    hasattr(self.field, "from_fields")
                    and name in self.field.from_fields
                ):
                    return True
                elif self.field.generated and any(
                    field_name == name
                    for field_name, *_ in Model._get_expr_references(
                        self.field.expression
                    )
                ):
                    return True
        # Check if this operation remotely references the field.
        if self.field is None:
            return False
        return bool(
            field_references(
                (app_label, self.model_name_lower),
                self.field,
                (app_label, model_name_lower),
                name,
            )
        )