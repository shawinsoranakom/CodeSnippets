def create_sql(self, model, schema_editor, using="", **kwargs):
        self.check_supported(schema_editor)
        statement = super().create_sql(
            model, schema_editor, using=" USING %s" % (using or self.suffix), **kwargs
        )
        with_params = self.get_with_params()
        if with_params:
            statement.parts["extra"] = " WITH (%s)%s" % (
                ", ".join(with_params),
                statement.parts["extra"],
            )
        return statement