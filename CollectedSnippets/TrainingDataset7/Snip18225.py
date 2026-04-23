def setUpTestData(cls):
        user = User.objects.create_user("jsmith", "jsmith@example.com", "pass")
        user = authenticate(username=user.username, password="pass")
        request = cls.request_factory.get("/somepath/")
        request.user = user
        cls.user, cls.request = user, request