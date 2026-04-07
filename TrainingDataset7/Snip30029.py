def test_bad_search_type(self):
        with self.assertRaisesMessage(
            ValueError, "Unknown search_type argument 'foo'."
        ):
            SearchQuery("kneecaps", search_type="foo")