def test_create_model_db_on_delete(self):
        class Parent(Model):
            class Meta:
                app_label = "schema"

        class Child(Model):
            parent_fk = ForeignKey(Parent, DB_SET_NULL, null=True)

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(Parent)
        with CaptureQueriesContext(connection) as ctx:
            with connection.schema_editor() as editor:
                editor.create_model(Child)

        self.assertForeignKeyNotExists(Child, "parent_id", "schema_parent")
        self.assertIs(
            any("ON DELETE" in query["sql"] for query in ctx.captured_queries), True
        )