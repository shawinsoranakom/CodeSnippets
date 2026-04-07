def setUpTestData(cls):
        User.objects.create_user(cls.TEST_USERNAME, cls.TEST_EMAIL, cls.TEST_PASSWORD)