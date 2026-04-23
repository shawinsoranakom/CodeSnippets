def reduce(self, operation, app_label):
        return super().reduce(operation, app_label) or self.can_reduce_through(
            operation, app_label
        )