def test_orm_query_without_autocommit(self):
        """
        #24921 -- ORM queries must be possible after set_autocommit(False).
        """
        Reporter.objects.create(first_name="Tintin")