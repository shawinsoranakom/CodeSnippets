def _check_field_name(self):
        if self.name == "pk":
            return []
        return [
            checks.Error(
                "'CompositePrimaryKey' must be named 'pk'.",
                obj=self,
                id="fields.E013",
            )
        ]