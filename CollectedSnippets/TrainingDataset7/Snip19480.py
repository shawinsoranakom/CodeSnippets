def test_check_view_not_class(self):
        self.assertEqual(
            check_url_config(None),
            [
                Error(
                    "Your URL pattern 'missing_as_view' has an invalid view, pass "
                    "EmptyCBV.as_view() instead of EmptyCBV.",
                    id="urls.E009",
                ),
            ],
        )