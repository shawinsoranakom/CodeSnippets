def setUpTestData(cls):
        cls.user1 = User.objects.create_user("test", "test@example.com", "test")
        cls.user1.is_active = False
        cls.user1.save()