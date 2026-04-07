def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="   ", password="secret", email="super@example.com"
        )
        cls.obj = CoverLetter.objects.create(author="             ")
        cls.change_link = reverse(
            "admin:admin_views_coverletter_change", args=(cls.obj.pk,)
        )