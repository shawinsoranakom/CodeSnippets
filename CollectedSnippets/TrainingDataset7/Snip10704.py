def create_sql(self, model, schema_editor):
        fields = [model._meta.get_field(field_name) for field_name in self.fields]
        include = [
            model._meta.get_field(field_name).column for field_name in self.include
        ]
        condition = self._get_condition_sql(model, schema_editor)
        expressions = self._get_index_expressions(model, schema_editor)
        return schema_editor._create_unique_sql(
            model,
            fields,
            self.name,
            condition=condition,
            deferrable=self.deferrable,
            include=include,
            opclasses=self.opclasses,
            expressions=expressions,
            nulls_distinct=self.nulls_distinct,
        )