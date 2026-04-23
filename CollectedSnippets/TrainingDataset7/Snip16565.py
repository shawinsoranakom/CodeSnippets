def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )
        self.p1 = PrePopulatedPost.objects.create(
            title="A Long Title", published=True, slug="a-long-title"
        )