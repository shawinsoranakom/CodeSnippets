def setUpTestData(cls):
        cls.site_2 = Site.objects.create(domain="example2.com", name="example2.com")
        cls.site_3 = Site.objects.create(domain="example3.com", name="example3.com")