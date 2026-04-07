def test_delete_without_redirect(self):
        msg = "No URL to redirect to. Provide a success_url."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.client.post("/edit/author/%s/delete/naive/" % self.author.pk)