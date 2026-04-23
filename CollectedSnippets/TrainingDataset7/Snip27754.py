def test_textchoices_functional_api(self):
        Medal = models.TextChoices("Medal", "GOLD SILVER BRONZE")
        self.assertEqual(Medal.labels, ["Gold", "Silver", "Bronze"])
        self.assertEqual(Medal.values, ["GOLD", "SILVER", "BRONZE"])
        self.assertEqual(Medal.names, ["GOLD", "SILVER", "BRONZE"])