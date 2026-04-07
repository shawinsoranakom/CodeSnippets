def reduce(self, operation, app_label):
        if (
            isinstance(operation, (AlterConstraint, RemoveConstraint))
            and self.model_name_lower == operation.model_name_lower
            and self.name == operation.name
        ):
            return [operation]
        return super().reduce(operation, app_label)