def test_tablespace_for_indexed_field(self):
        sql = sql_for_table(Article).lower()
        if settings.DEFAULT_INDEX_TABLESPACE:
            # 1 for the table
            self.assertNumContains(sql, "tbl_tbsp", 1)
            # 1 for the primary key + 1 for the index on code
            self.assertNumContains(sql, settings.DEFAULT_INDEX_TABLESPACE, 2)
        else:
            # 1 for the table + 1 for the primary key + 1 for the index on code
            self.assertNumContains(sql, "tbl_tbsp", 3)

        # 1 for the index on reference
        self.assertNumContains(sql, "idx_tbsp", 1)