def setUpTestData(cls):
        cls.tenant = Tenant.objects.create()
        cls.user = User.objects.create(
            tenant=cls.tenant,
            id=1,
            email="user0001@example.com",
        )
        cls.comment = Comment.objects.create(tenant=cls.tenant, id=1, user=cls.user)