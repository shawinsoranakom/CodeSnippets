def test_get_url(self):
        rel = Album._meta.get_field("band")
        w = AutocompleteSelect(rel, admin.site)
        url = w.get_url()
        self.assertEqual(url, "/autocomplete/")