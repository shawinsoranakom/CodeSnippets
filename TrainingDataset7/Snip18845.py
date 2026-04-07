def test_integrity_checks_on_creation(self):
        """
        Try to create a model instance that violates a FK constraint. If it
        fails it should fail with IntegrityError.
        """
        a1 = Article(
            headline="This is a test",
            pub_date=datetime.datetime(2005, 7, 27),
            reporter_id=30,
        )
        try:
            a1.save()
        except IntegrityError:
            pass
        else:
            self.skipTest("This backend does not support integrity checks.")
        # Now that we know this backend supports integrity checks we make sure
        # constraints are also enforced for proxy  Refs #17519
        a2 = Article(
            headline="This is another test",
            reporter=self.r,
            pub_date=datetime.datetime(2012, 8, 3),
            reporter_proxy_id=30,
        )
        with self.assertRaises(IntegrityError):
            a2.save()