def clean(self):
        if self.name1 == "FORBIDDEN_VALUE":
            raise ValidationError(
                {"name1": [ValidationError("Model.clean() error messages.")]}
            )
        elif self.name1 == "FORBIDDEN_VALUE2":
            raise ValidationError(
                {"name1": "Model.clean() error messages (simpler syntax)."}
            )
        elif self.name1 == "GLOBAL_ERROR":
            raise ValidationError("Global error message.")