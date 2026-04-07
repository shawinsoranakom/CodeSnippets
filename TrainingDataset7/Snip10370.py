def reduce(self, operation, app_label):
        if (
            isinstance(operation, RemoveConstraint)
            and self.model_name_lower == operation.model_name_lower
            and self.constraint.name == operation.name
        ):
            return []
        if (
            isinstance(operation, AlterConstraint)
            and self.model_name_lower == operation.model_name_lower
            and self.constraint.name == operation.name
        ):
            return [replace(self, constraint=operation.constraint)]
        return super().reduce(operation, app_label)