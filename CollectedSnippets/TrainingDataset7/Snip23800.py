def test_create_without_redirect(self):
        msg = (
            "No URL to redirect to. Either provide a url or define a "
            "get_absolute_url method on the Model."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.client.post(
                "/edit/authors/create/naive/",
                {"name": "Randall Munroe", "slug": "randall-munroe"},
            )