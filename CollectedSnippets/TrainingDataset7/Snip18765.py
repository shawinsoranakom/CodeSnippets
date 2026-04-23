def setUp(self):
        def create_foreign_key_name(table_name, column_names, suffix):
            return ", ".join(
                "%s_%s_%s" % (table_name, column_name, suffix)
                for column_name in column_names
            )

        self.reference = ForeignKeyName(
            "table",
            ["first_column", "second_column"],
            "to_table",
            ["to_first_column", "to_second_column"],
            "%(to_table)s_%(to_column)s_fk",
            create_foreign_key_name,
        )