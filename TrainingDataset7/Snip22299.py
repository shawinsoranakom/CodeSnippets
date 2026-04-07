def setUpTestData(cls):
        # don't use the manager because we want to ensure the site exists
        # with pk=1, regardless of whether or not it already exists.
        cls.site1 = Site(pk=1, domain="example.com", name="example.com")
        cls.site1.save()