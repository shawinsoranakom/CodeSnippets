def test_integrity_checks_on_update(self):
        """
        Try to update a model instance introducing a FK constraint violation.
        If it fails it should fail with IntegrityError.
        """
        # Create an Article.
        Article.objects.create(
            headline="Test article",
            pub_date=datetime.datetime(2010, 9, 4),
            reporter=self.r,
        )
        # Retrieve it from the DB
        a1 = Article.objects.get(headline="Test article")
        a1.reporter_id = 30
        try:
            a1.save()
        except IntegrityError:
            pass
        else:
            self.skipTest("This backend does not support integrity checks.")
        # Now that we know this backend supports integrity checks we make sure
        # constraints are also enforced for proxy  Refs #17519
        # Create another article
        r_proxy = ReporterProxy.objects.get(pk=self.r.pk)
        Article.objects.create(
            headline="Another article",
            pub_date=datetime.datetime(1988, 5, 15),
            reporter=self.r,
            reporter_proxy=r_proxy,
        )
        # Retrieve the second article from the DB
        a2 = Article.objects.get(headline="Another article")
        a2.reporter_proxy_id = 30
        with self.assertRaises(IntegrityError):
            a2.save()