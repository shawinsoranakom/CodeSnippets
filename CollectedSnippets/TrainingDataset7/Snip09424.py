def _delete_constraint_sql(self, template, model, name):
        return Statement(
            template,
            table=Table(model._meta.db_table, self.quote_name),
            name=self.quote_name(name),
        )