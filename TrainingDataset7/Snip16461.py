def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        cls.v1 = Villain.objects.create(name="Adam")
        cls.pl3 = Plot.objects.create(
            name="Corn Conspiracy", team_leader=cls.v1, contact=cls.v1
        )