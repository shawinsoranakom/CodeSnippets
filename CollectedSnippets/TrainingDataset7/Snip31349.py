def test_alter_field_fk_keeps_index(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(Book)
        expected_fks = (
            1
            if connection.features.supports_foreign_keys
            and connection.features.can_introspect_foreign_keys
            else 0
        )
        expected_indexes = 1 if connection.features.indexes_foreign_keys else 0

        # Check the index is right to begin with.
        counts = self.get_constraints_count(
            Book._meta.db_table,
            Book._meta.get_field("author").column,
            (Author._meta.db_table, Author._meta.pk.column),
        )
        self.assertEqual(
            counts,
            {"fks": expected_fks, "uniques": 0, "indexes": expected_indexes},
        )

        old_field = Book._meta.get_field("author")
        # on_delete changed from CASCADE.
        new_field = ForeignKey(Author, PROTECT)
        new_field.set_attributes_from_name("author")
        with connection.schema_editor() as editor:
            editor.alter_field(Book, old_field, new_field, strict=True)

        counts = self.get_constraints_count(
            Book._meta.db_table,
            Book._meta.get_field("author").column,
            (Author._meta.db_table, Author._meta.pk.column),
        )
        # The index remains.
        self.assertEqual(
            counts,
            {"fks": expected_fks, "uniques": 0, "indexes": expected_indexes},
        )