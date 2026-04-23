def reduce(self, operation, app_label):
        if (
            isinstance(operation, (self.__class__, DeleteModel))
            and self.name_lower == operation.name_lower
        ):
            return [operation]
        return super().reduce(operation, app_label)