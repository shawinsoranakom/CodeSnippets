def test_update_without_redirect(self):
        msg = (
            "No URL to redirect to. Either provide a url or define a "
            "get_absolute_url method on the Model."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.client.post(
                "/edit/author/%s/update/naive/" % self.author.pk,
                {"name": "Randall Munroe (author of xkcd)", "slug": "randall-munroe"},
            )