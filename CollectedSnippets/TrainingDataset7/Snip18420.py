def setUp(self):
        self.login()
        # Get the latest last_login value.
        self.admin = User.objects.get(pk=self.u1.pk)