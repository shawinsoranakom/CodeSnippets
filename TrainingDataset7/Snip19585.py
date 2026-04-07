def setUpTestData(cls):
        cls.tenant = Tenant.objects.create(id=1)
        cls.user = User.objects.create(
            tenant=cls.tenant,
            id=1,
            email="user0001@example.com",
        )