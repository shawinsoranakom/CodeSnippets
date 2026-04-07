def test_same_manager_queries(self):
        """
        The MyPerson model should be generating the same database queries as
        the Person model (when the same manager is used in each case).
        """
        my_person_sql = (
            MyPerson.other.all().query.get_compiler(DEFAULT_DB_ALIAS).as_sql()
        )
        person_sql = (
            Person.objects.order_by("name")
            .query.get_compiler(DEFAULT_DB_ALIAS)
            .as_sql()
        )
        self.assertEqual(my_person_sql, person_sql)