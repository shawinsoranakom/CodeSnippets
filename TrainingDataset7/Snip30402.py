def setUpTestData(cls):
        cls.category = DumbCategory.objects.create()
        cls.proxy_category = ProxyCategory.objects.create()