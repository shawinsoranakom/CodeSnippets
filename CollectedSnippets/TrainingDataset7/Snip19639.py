def setUpTestData(cls):
        cls.tenant = Tenant.objects.create()
        cls.user = User.objects.create(
            tenant=cls.tenant, id=1, email="exclude@example.com"
        )