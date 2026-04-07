def generate_removed_indexes(self):
        for (app_label, model_name), alt_indexes in self.altered_indexes.items():
            for index in alt_indexes["removed_indexes"]:
                self.add_operation(
                    app_label,
                    operations.RemoveIndex(
                        model_name=model_name,
                        name=index.name,
                    ),
                )