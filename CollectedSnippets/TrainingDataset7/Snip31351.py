def test_alter_field_o2o_keeps_unique(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(BookWithO2O)
        expected_fks = (
            1
            if connection.features.supports_foreign_keys
            and connection.features.can_introspect_foreign_keys
            else 0
        )

        # Check the unique constraint is right to begin with.
        counts = self.get_constraints_count(
            BookWithO2O._meta.db_table,
            BookWithO2O._meta.get_field("author").column,
            (Author._meta.db_table, Author._meta.pk.column),
        )
        self.assertEqual(counts, {"fks": expected_fks, "uniques": 1, "indexes": 0})

        old_field = BookWithO2O._meta.get_field("author")
        # on_delete changed from CASCADE.
        new_field = OneToOneField(Author, PROTECT)
        new_field.set_attributes_from_name("author")
        with connection.schema_editor() as editor:
            editor.alter_field(BookWithO2O, old_field, new_field, strict=True)

        counts = self.get_constraints_count(
            BookWithO2O._meta.db_table,
            BookWithO2O._meta.get_field("author").column,
            (Author._meta.db_table, Author._meta.pk.column),
        )
        # The unique constraint remains.
        self.assertEqual(counts, {"fks": expected_fks, "uniques": 1, "indexes": 0})