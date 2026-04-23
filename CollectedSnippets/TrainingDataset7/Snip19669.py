def setUpTestData(cls):
        cls.tenant_1 = Tenant.objects.create(name="A")
        cls.tenant_2 = Tenant.objects.create(name="B")
        cls.user_1 = User.objects.create(
            tenant=cls.tenant_1,
            id=1,
            email="user0001@example.com",
        )
        cls.user_2 = User.objects.create(
            tenant=cls.tenant_1,
            id=2,
            email="user0002@example.com",
        )
        cls.user_3 = User.objects.create(
            tenant=cls.tenant_2,
            id=3,
            email="user0003@example.com",
        )
        cls.comment_1 = Comment.objects.create(id=1, user=cls.user_1)
        cls.comment_2 = Comment.objects.create(id=2, user=cls.user_1)
        cls.comment_3 = Comment.objects.create(id=3, user=cls.user_2)
        cls.token_1 = Token.objects.create(id=1, tenant=cls.tenant_1)
        cls.token_2 = Token.objects.create(id=2, tenant=cls.tenant_2)
        cls.token_3 = Token.objects.create(id=3, tenant=cls.tenant_1)
        cls.token_4 = Token.objects.create(id=4, tenant=cls.tenant_2)