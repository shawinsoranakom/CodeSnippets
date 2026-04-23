def test_orm_query_after_error_and_rollback(self):
        """
        ORM queries are allowed after an error and a rollback in non-autocommit
        mode (#27504).
        """
        r1 = Reporter.objects.create(first_name="Archibald", last_name="Haddock")
        r2 = Reporter(first_name="Cuthbert", last_name="Calculus", id=r1.id)
        with self.assertRaises(IntegrityError):
            r2.save(force_insert=True)
        transaction.rollback()
        Reporter.objects.last()