def setUp(self):
        self.client.force_login(self.superuser)
        with captured_stderr() as self.docutils_stderr:
            self.response = self.client.get(
                reverse("django-admindocs-models-detail", args=["admin_docs", "Person"])
            )