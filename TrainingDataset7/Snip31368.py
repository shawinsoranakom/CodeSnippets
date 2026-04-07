def test_db_default_output_field_resolving(self):
        class Author(Model):
            data = JSONField(
                encoder=DjangoJSONEncoder,
                db_default={
                    "epoch": datetime.datetime(1970, 1, 1, tzinfo=datetime.UTC)
                },
            )

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(Author)

        author = Author.objects.create()
        author.refresh_from_db()
        self.assertEqual(author.data, {"epoch": "1970-01-01T00:00:00Z"})