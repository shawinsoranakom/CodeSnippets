def setUpTestData(cls):
        super().setUpTestData()
        cls.tenant_1 = Tenant.objects.create()
        cls.tenant_2 = Tenant.objects.create()
        cls.user_1 = User.objects.create(
            tenant=cls.tenant_1, id=1, email=cls.USER_1_EMAIL
        )
        cls.user_2 = User.objects.create(
            tenant=cls.tenant_1, id=2, email=cls.USER_2_EMAIL
        )
        cls.user_3 = User.objects.create(
            tenant=cls.tenant_2, id=3, email=cls.USER_3_EMAIL
        )
        cls.post_1 = Post.objects.create(tenant=cls.tenant_1, id=cls.POST_1_ID)
        cls.post_2 = Post.objects.create(tenant=cls.tenant_1, id=cls.POST_2_ID)
        cls.post_3 = Post.objects.create(tenant=cls.tenant_2, id=cls.POST_3_ID)