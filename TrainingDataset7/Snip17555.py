def setUpTestData(cls):
        cls.user = User.objects.create_user("test", "test@example.com", "test")