def setUpTestData(cls):
        cls.user1 = User.objects.create_user("test", "test@example.com", "test")