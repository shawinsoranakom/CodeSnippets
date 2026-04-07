def generate_added_indexes(self):
        for (app_label, model_name), alt_indexes in self.altered_indexes.items():
            dependencies = self._get_dependencies_for_model(app_label, model_name)
            for index in alt_indexes["added_indexes"]:
                self.add_operation(
                    app_label,
                    operations.AddIndex(
                        model_name=model_name,
                        index=index,
                    ),
                    dependencies=dependencies,
                )