def test_indexed_charfield_to_textfield(self):
        class SimpleModel(Model):
            field1 = CharField(max_length=10, db_index=True)

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(SimpleModel)
        self.assertEqual(
            self.get_constraints_for_column(SimpleModel, "field1"),
            [
                "schema_simplemodel_field1_f07a3d6a",
                "schema_simplemodel_field1_f07a3d6a_like",
            ],
        )
        # Change to TextField.
        old_field1 = SimpleModel._meta.get_field("field1")
        new_field1 = TextField(db_index=True)
        new_field1.set_attributes_from_name("field1")
        with connection.schema_editor() as editor:
            editor.alter_field(SimpleModel, old_field1, new_field1, strict=True)
        self.assertEqual(
            self.get_constraints_for_column(SimpleModel, "field1"),
            [
                "schema_simplemodel_field1_f07a3d6a",
                "schema_simplemodel_field1_f07a3d6a_like",
            ],
        )
        # Change back to CharField.
        old_field1 = SimpleModel._meta.get_field("field1")
        new_field1 = CharField(max_length=10, db_index=True)
        new_field1.set_attributes_from_name("field1")
        with connection.schema_editor() as editor:
            editor.alter_field(SimpleModel, old_field1, new_field1, strict=True)
        self.assertEqual(
            self.get_constraints_for_column(SimpleModel, "field1"),
            [
                "schema_simplemodel_field1_f07a3d6a",
                "schema_simplemodel_field1_f07a3d6a_like",
            ],
        )