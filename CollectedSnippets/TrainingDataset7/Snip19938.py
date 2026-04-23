def test_multidb(self):
        """
        When using multiple databases, ContentType.objects.get_for_model() uses
        db_for_read().
        """
        ContentType.objects.clear_cache()
        with (
            self.assertNumQueries(0, using="default"),
            self.assertNumQueries(1, using="other"),
        ):
            ContentType.objects.get_for_model(Author)