def can_reduce_through(self, operation, app_label):
        return super().can_reduce_through(operation, app_label) or (
            isinstance(operation, AlterTogetherOptionOperation)
            and type(operation) is not type(self)
        )