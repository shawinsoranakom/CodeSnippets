def setUpTestData(cls):
        cls.site = Site(id=settings.SITE_ID, domain="example.com", name="example.com")
        cls.site.save()