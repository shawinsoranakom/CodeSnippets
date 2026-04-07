def is_same_field_operation(self, operation):
        return (
            self.is_same_model_operation(operation)
            and self.name_lower == operation.name_lower
        )