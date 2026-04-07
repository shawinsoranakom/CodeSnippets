def test_db_comments_from_abstract_model(self):
        class AbstractModelWithDbComments(Model):
            name = CharField(
                max_length=255, db_comment="Custom comment", null=True, blank=True
            )

            class Meta:
                app_label = "schema"
                abstract = True
                db_table_comment = "Custom table comment"

        class ModelWithDbComments(AbstractModelWithDbComments):
            pass

        with connection.schema_editor() as editor:
            editor.create_model(ModelWithDbComments)
        self.isolated_local_models = [ModelWithDbComments]

        self.assertEqual(
            self.get_column_comment(ModelWithDbComments._meta.db_table, "name"),
            "Custom comment",
        )
        self.assertEqual(
            self.get_table_comment(ModelWithDbComments._meta.db_table),
            "Custom table comment",
        )