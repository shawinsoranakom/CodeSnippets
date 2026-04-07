def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email=None
        )
        cls.u2 = User.objects.create_user(username="testser", password="secret")
        Car.objects.create(owner=cls.superuser, make="Volkswagen", model="Passat")
        Car.objects.create(owner=cls.u2, make="BMW", model="M3")