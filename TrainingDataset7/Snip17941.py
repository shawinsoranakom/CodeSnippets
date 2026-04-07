def setUpTestData(cls):
        cls.user = User.objects.create_user(username="joe", password="qwerty")