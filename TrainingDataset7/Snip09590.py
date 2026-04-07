def remove_index(self, model, index):
        self._create_missing_fk_index(
            model,
            fields=[field_name for field_name, _ in index.fields_orders],
            expressions=index.expressions,
        )
        super().remove_index(model, index)