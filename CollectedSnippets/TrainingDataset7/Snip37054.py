def test_index_subdir(self):
        response = self.client.get("/%s/subdir/" % self.prefix)
        self.assertContains(response, "Index of subdir/")
        # File with a leading dot (e.g. .hidden) aren't displayed.
        self.assertEqual(response.context["file_list"], ["visible"])