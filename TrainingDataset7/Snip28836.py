def test_tablespace_for_many_to_many_field(self):
        sql = sql_for_table(Authors).lower()
        # The join table of the ManyToManyField goes to the model's tablespace,
        # and its indexes too, unless DEFAULT_INDEX_TABLESPACE is set.
        if settings.DEFAULT_INDEX_TABLESPACE:
            # 1 for the table
            self.assertNumContains(sql, "tbl_tbsp", 1)
            # 1 for the primary key
            self.assertNumContains(sql, settings.DEFAULT_INDEX_TABLESPACE, 1)
        else:
            # 1 for the table + 1 for the index on the primary key
            self.assertNumContains(sql, "tbl_tbsp", 2)
        self.assertNumContains(sql, "idx_tbsp", 0)

        sql = sql_for_index(Authors).lower()
        # The ManyToManyField declares no db_tablespace, its indexes go to
        # the model's tablespace, unless DEFAULT_INDEX_TABLESPACE is set.
        if settings.DEFAULT_INDEX_TABLESPACE:
            self.assertNumContains(sql, settings.DEFAULT_INDEX_TABLESPACE, 2)
        else:
            self.assertNumContains(sql, "tbl_tbsp", 2)
        self.assertNumContains(sql, "idx_tbsp", 0)

        sql = sql_for_table(Reviewers).lower()
        # The join table of the ManyToManyField goes to the model's tablespace,
        # and its indexes too, unless DEFAULT_INDEX_TABLESPACE is set.
        if settings.DEFAULT_INDEX_TABLESPACE:
            # 1 for the table
            self.assertNumContains(sql, "tbl_tbsp", 1)
            # 1 for the primary key
            self.assertNumContains(sql, settings.DEFAULT_INDEX_TABLESPACE, 1)
        else:
            # 1 for the table + 1 for the index on the primary key
            self.assertNumContains(sql, "tbl_tbsp", 2)
        self.assertNumContains(sql, "idx_tbsp", 0)

        sql = sql_for_index(Reviewers).lower()
        # The ManyToManyField declares db_tablespace, its indexes go there.
        self.assertNumContains(sql, "tbl_tbsp", 0)
        self.assertNumContains(sql, "idx_tbsp", 2)