def test_jsoni18n(self):
        """
        The json_catalog returns the language catalog and settings as JSON.
        """
        with override("de"):
            response = self.client.get("/jsoni18n/")
            data = json.loads(response.text)
            self.assertIn("catalog", data)
            self.assertIn("formats", data)
            self.assertEqual(
                data["formats"]["TIME_INPUT_FORMATS"],
                ["%H:%M:%S", "%H:%M:%S.%f", "%H:%M"],
            )
            self.assertEqual(data["formats"]["FIRST_DAY_OF_WEEK"], 1)
            self.assertIn("plural", data)
            self.assertEqual(data["catalog"]["month name\x04May"], "Mai")
            self.assertIn("DATETIME_FORMAT", data["formats"])
            self.assertEqual(data["plural"], "(n != 1)")