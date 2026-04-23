def setUpTestData(cls):
        Site.objects.get_or_create(
            id=settings.SITE_ID, domain="example.com", name="example.com"
        )
        Site.objects.create(
            id=settings.SITE_ID + 1, domain="example2.com", name="example2.com"
        )