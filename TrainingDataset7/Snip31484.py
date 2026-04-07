def test_db_comment_table_unsupported(self):
        class ModelWithDbTableComment(Model):
            class Meta:
                app_label = "schema"
                db_table_comment = "Custom table comment"

        # Table comments are ignored on databases that don't support them.
        with connection.schema_editor() as editor, self.assertNumQueries(1):
            editor.create_model(ModelWithDbTableComment)
        self.isolated_local_models = [ModelWithDbTableComment]
        with connection.schema_editor() as editor, self.assertNumQueries(0):
            editor.alter_db_table_comment(
                ModelWithDbTableComment, "Custom table comment", "New table comment"
            )