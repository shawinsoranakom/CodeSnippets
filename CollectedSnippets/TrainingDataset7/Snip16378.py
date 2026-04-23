def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        cls.per1 = Person.objects.create(name="John Mauchly", gender=1, alive=True)