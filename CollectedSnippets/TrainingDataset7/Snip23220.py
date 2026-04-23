def test_options(self):
        options = list(
            self.widget(choices=self.beatles).options(
                "name",
                ["J"],
                attrs={"class": "super"},
            )
        )
        self.assertEqual(len(options), 4)
        self.assertEqual(options[0]["name"], "name")
        self.assertEqual(options[0]["value"], "J")
        self.assertEqual(options[0]["label"], "John")
        self.assertEqual(options[0]["index"], "0")
        self.assertIs(options[0]["selected"], True)
        # Template-related attributes
        self.assertEqual(options[1]["name"], "name")
        self.assertEqual(options[1]["value"], "P")
        self.assertEqual(options[1]["label"], "Paul")
        self.assertEqual(options[1]["index"], "1")
        self.assertIs(options[1]["selected"], False)