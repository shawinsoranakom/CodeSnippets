def setUpTestData(cls):
        cls.site = Site.objects.get(pk=settings.SITE_ID)