def test_multivaluedict(self):
        d = MultiValueDict(
            {"name": ["Adrian", "Simon"], "position": ["Developer"], "empty": []}
        )
        self.assertEqual(d["name"], "Simon")
        self.assertEqual(d.get("name"), "Simon")
        self.assertEqual(d.getlist("name"), ["Adrian", "Simon"])
        self.assertEqual(
            list(d.items()),
            [("name", "Simon"), ("position", "Developer"), ("empty", [])],
        )
        self.assertEqual(
            list(d.lists()),
            [("name", ["Adrian", "Simon"]), ("position", ["Developer"]), ("empty", [])],
        )
        with self.assertRaisesMessage(MultiValueDictKeyError, "'lastname'"):
            d.__getitem__("lastname")
        self.assertIsNone(d.get("empty"))
        self.assertEqual(d.get("empty", "nonexistent"), "nonexistent")
        self.assertIsNone(d.get("lastname"))
        self.assertEqual(d.get("lastname", "nonexistent"), "nonexistent")
        self.assertEqual(d.getlist("lastname"), [])
        self.assertEqual(
            d.getlist("doesnotexist", ["Adrian", "Simon"]), ["Adrian", "Simon"]
        )
        d.setlist("lastname", ["Holovaty", "Willison"])
        self.assertEqual(d.getlist("lastname"), ["Holovaty", "Willison"])
        self.assertEqual(list(d.values()), ["Simon", "Developer", [], "Willison"])

        d.setlistdefault("lastname", ["Doe"])
        self.assertEqual(d.getlist("lastname"), ["Holovaty", "Willison"])
        d.setlistdefault("newkey", ["Doe"])
        self.assertEqual(d.getlist("newkey"), ["Doe"])