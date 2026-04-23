def test_inheritance_new_table(self):
        """
        The StatusPerson models should have its own table (it's using ORM-level
        inheritance).
        """
        sp_sql = (
            StatusPerson.objects.all().query.get_compiler(DEFAULT_DB_ALIAS).as_sql()
        )
        p_sql = Person.objects.all().query.get_compiler(DEFAULT_DB_ALIAS).as_sql()
        self.assertNotEqual(sp_sql, p_sql)