def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        cls.p1 = PrePopulatedPost.objects.create(
            title="A Long Title", published=True, slug="a-long-title"
        )