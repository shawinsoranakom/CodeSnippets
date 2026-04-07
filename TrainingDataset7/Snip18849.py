def test_check_constraints(self):
        """
        Constraint checks should raise an IntegrityError when bad data is in
        the DB.
        """
        with transaction.atomic():
            # Create an Article.
            Article.objects.create(
                headline="Test article",
                pub_date=datetime.datetime(2010, 9, 4),
                reporter=self.r,
            )
            # Retrieve it from the DB
            a = Article.objects.get(headline="Test article")
            a.reporter_id = 30
            with connection.constraint_checks_disabled():
                a.save()
                try:
                    connection.check_constraints(table_names=[Article._meta.db_table])
                except IntegrityError:
                    pass
                else:
                    self.skipTest("This backend does not support integrity checks.")
            transaction.set_rollback(True)