def test_index_error_not_suppressed(self):
        """
        #23555 -- Unexpected IndexError exceptions in QuerySet iteration
        shouldn't be suppressed.
        """

        def check():
            # We know that we've broken the __iter__ method, so the queryset
            # should always raise an exception.
            with self.assertRaises(IndexError):
                IndexErrorArticle.objects.all()[:10:2]
            with self.assertRaises(IndexError):
                IndexErrorArticle.objects.first()
            with self.assertRaises(IndexError):
                IndexErrorArticle.objects.last()

        check()

        # And it does not matter if there are any records in the DB.
        IndexErrorArticle.objects.create(
            headline="Article 1",
            pub_date=datetime(2005, 7, 26),
            expire_date=datetime(2005, 9, 1),
        )
        check()