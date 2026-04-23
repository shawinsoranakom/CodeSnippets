def setUpTestData(cls):
        super().setUpTestData()
        # Make me a superuser before logging in.
        User.objects.filter(username="testclient").update(
            is_staff=True, is_superuser=True
        )