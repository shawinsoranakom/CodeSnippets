def test_flatatt(self):
        ###########
        # flatatt #
        ###########

        self.assertEqual(flatatt({"id": "header"}), ' id="header"')
        self.assertEqual(
            flatatt({"class": "news", "title": "Read this"}),
            ' class="news" title="Read this"',
        )
        self.assertEqual(
            flatatt({"class": "news", "title": "Read this", "required": "required"}),
            ' class="news" required="required" title="Read this"',
        )
        self.assertEqual(
            flatatt({"class": "news", "title": "Read this", "required": True}),
            ' class="news" title="Read this" required',
        )
        self.assertEqual(
            flatatt({"class": "news", "title": "Read this", "required": False}),
            ' class="news" title="Read this"',
        )
        self.assertEqual(flatatt({"class": None}), "")
        self.assertEqual(flatatt({}), "")