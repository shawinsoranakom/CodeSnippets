def test_unique_name_quoting(self):
        old_table_name = TagUniqueRename._meta.db_table
        try:
            with connection.schema_editor() as editor:
                editor.create_model(TagUniqueRename)
                editor.alter_db_table(TagUniqueRename, old_table_name, "unique-table")
                TagUniqueRename._meta.db_table = "unique-table"
                # This fails if the unique index name isn't quoted.
                editor.alter_unique_together(TagUniqueRename, [], (("title", "slug2"),))
        finally:
            with connection.schema_editor() as editor:
                editor.delete_model(TagUniqueRename)
            TagUniqueRename._meta.db_table = old_table_name