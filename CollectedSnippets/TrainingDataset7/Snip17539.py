def setUpTestData(cls):
        cls.user1 = User.objects.create_user("test", "test@example.com", "test")
        cls.user2 = User.objects.create_user("test2", "test2@example.com", "test")
        cls.user3 = User.objects.create_user("test3", "test3@example.com", "test")