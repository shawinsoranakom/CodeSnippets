def test_index(self):
        response = self.client.get("/%s/" % self.prefix)
        self.assertContains(response, "Index of ./")
        # Directories have a trailing slash.
        self.assertIn("subdir/", response.context["file_list"])