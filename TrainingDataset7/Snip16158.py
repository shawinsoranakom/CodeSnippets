def setUpTestData(cls):
        cls.s1 = ExternalSubscriber.objects.create(
            name="John Doe", email="john@example.org"
        )
        cls.s2 = Subscriber.objects.create(
            name="Max Mustermann", email="max@example.org"
        )
        cls.user = User.objects.create_user(
            username="user",
            password="secret",
            email="user@example.com",
            is_staff=True,
        )
        permission = Permission.objects.get(codename="change_subscriber")
        cls.user.user_permissions.add(permission)