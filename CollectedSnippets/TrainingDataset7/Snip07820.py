def reduce(self, operation, app_label):
        if isinstance(operation, RemoveCollation) and self.name == operation.name:
            return []
        return super().reduce(operation, app_label)