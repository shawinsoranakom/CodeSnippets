def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        cls.s1 = ExternalSubscriber.objects.create(
            name="John Doe", email="john@example.org"
        )
        cls.s2 = Subscriber.objects.create(
            name="Max Mustermann", email="max@example.org"
        )