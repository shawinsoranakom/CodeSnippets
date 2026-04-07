def setUpTestData(cls):
        cls.user = models.User.objects.create(username="joe", password="qwerty")