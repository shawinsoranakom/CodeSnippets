def setUpTestData(cls):
        User.objects.create_user(
            username="inactive", password="password", is_active=False
        )