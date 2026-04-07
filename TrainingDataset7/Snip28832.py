def test_tablespace_for_model(self):
        sql = sql_for_table(Scientist).lower()
        if settings.DEFAULT_INDEX_TABLESPACE:
            # 1 for the table
            self.assertNumContains(sql, "tbl_tbsp", 1)
            # 1 for the index on the primary key
            self.assertNumContains(sql, settings.DEFAULT_INDEX_TABLESPACE, 1)
        else:
            # 1 for the table + 1 for the index on the primary key
            self.assertNumContains(sql, "tbl_tbsp", 2)