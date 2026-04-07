def setUpTestData(cls):
        Site(id=settings.SITE_ID, domain="example.com", name="example.com").save()