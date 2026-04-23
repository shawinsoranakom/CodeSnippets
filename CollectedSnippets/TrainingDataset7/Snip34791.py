def test_urlconf_was_changed(self):
        "TestCase can enforce a custom URLconf on a per-test basis"
        url = reverse("arg_view", args=["somename"])
        self.assertEqual(url, "/arg_view/somename/")