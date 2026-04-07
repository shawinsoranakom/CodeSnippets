def test_manager_class_caching(self):
        r1 = Reporter.objects.create(first_name="Mike")
        r2 = Reporter.objects.create(first_name="John")

        # Same twice
        self.assertIs(r1.article_set.__class__, r1.article_set.__class__)

        # Same as each other
        self.assertIs(r1.article_set.__class__, r2.article_set.__class__)