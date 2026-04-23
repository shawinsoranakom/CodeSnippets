def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="super",
            password="secret",
            email="super@example.com",
        )
        for i in range(1, 1101):
            LogEntry.objects.log_actions(
                self.superuser.pk,
                [self.superuser],
                CHANGE,
                change_message=f"Changed something {i}",
            )
        self.admin_login(
            username="super",
            password="secret",
            login_url=reverse("admin:index"),
        )