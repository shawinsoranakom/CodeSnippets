def test_add_foreign_object(self):
        with connection.schema_editor() as editor:
            editor.create_model(BookForeignObj)
        self.local_models = [BookForeignObj]

        new_field = ForeignObject(
            Author, on_delete=CASCADE, from_fields=["author_id"], to_fields=["id"]
        )
        new_field.set_attributes_from_name("author")
        with connection.schema_editor() as editor:
            editor.add_field(BookForeignObj, new_field)