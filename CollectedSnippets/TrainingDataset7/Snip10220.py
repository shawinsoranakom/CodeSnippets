def reduce(self, operation, app_label):
        return super().reduce(operation, app_label) or not operation.references_field(
            self.model_name, self.name, app_label
        )