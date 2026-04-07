def reduce(self, operation, app_label):
        if isinstance(operation, RemoveIndex) and self.index.name == operation.name:
            return []
        if isinstance(operation, RenameIndex) and self.index.name == operation.old_name:
            index = copy(self.index)
            index.name = operation.new_name
            return [replace(self, index=index)]
        return super().reduce(operation, app_label)