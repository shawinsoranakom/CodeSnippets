def test_sql_insert_compiler_return_id_attribute(self):
        """
        Regression test for #14019: SQLInsertCompiler.as_sql() failure
        """
        db = router.db_for_write(Party)
        query = InsertQuery(Party)
        query.insert_values([Party._meta.fields[0]], [], raw=False)
        # this line will raise an AttributeError without the accompanying fix
        query.get_compiler(using=db).as_sql()