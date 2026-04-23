def test_search_with_spaces(self):
        url = reverse("admin:admin_views_person_changelist") + "?q=%s"
        tests = [
            ('"John Doe"', 1),
            ("'John Doe'", 1),
            ("John Doe", 0),
            ('"John Doe" John', 1),
            ("'John Doe' John", 1),
            ("John Doe John", 0),
            ('"John Do"', 1),
            ("'John Do'", 1),
            ("'John O'Hara'", 0),
            ("'John O\\'Hara'", 1),
            ('"John O"Hara"', 0),
            ('"John O\\"Hara"', 1),
        ]
        for search, hits in tests:
            with self.subTest(search=search):
                response = self.client.get(url % search)
                self.assertContains(response, "\n%s person" % hits)