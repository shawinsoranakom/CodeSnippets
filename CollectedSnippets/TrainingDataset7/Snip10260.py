def can_reduce_through(self, operation, app_label):
        return not operation.references_model(self.name, app_label)