def test_get_absolute_url_with_hardcoded_url(self):
        fp = FlatPage(title="Test", url="/hardcoded/")
        self.assertEqual(fp.get_absolute_url(), "/flatpage/")