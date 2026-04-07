def test_db_comment_table(self):
        class ModelWithDbTableComment(Model):
            class Meta:
                app_label = "schema"
                db_table_comment = "Custom table comment"

        with connection.schema_editor() as editor:
            editor.create_model(ModelWithDbTableComment)
        self.isolated_local_models = [ModelWithDbTableComment]
        self.assertEqual(
            self.get_table_comment(ModelWithDbTableComment._meta.db_table),
            "Custom table comment",
        )
        # Alter table comment.
        old_db_table_comment = ModelWithDbTableComment._meta.db_table_comment
        with connection.schema_editor() as editor:
            editor.alter_db_table_comment(
                ModelWithDbTableComment, old_db_table_comment, "New table comment"
            )
        self.assertEqual(
            self.get_table_comment(ModelWithDbTableComment._meta.db_table),
            "New table comment",
        )
        # Remove table comment.
        old_db_table_comment = ModelWithDbTableComment._meta.db_table_comment
        with connection.schema_editor() as editor:
            editor.alter_db_table_comment(
                ModelWithDbTableComment, old_db_table_comment, None
            )
        self.assertIn(
            self.get_table_comment(ModelWithDbTableComment._meta.db_table),
            [None, ""],
        )