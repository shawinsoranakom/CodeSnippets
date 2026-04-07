def test_jsoni18n_with_missing_en_files(self):
        """
        Same as above for the json_catalog view. Here we also check for the
        expected JSON format.
        """
        with self.settings(LANGUAGE_CODE="es"), override("en-us"):
            response = self.client.get("/jsoni18n/")
            data = json.loads(response.text)
            self.assertIn("catalog", data)
            self.assertIn("formats", data)
            self.assertIn("plural", data)
            self.assertEqual(data["catalog"], {})
            self.assertIn("DATETIME_FORMAT", data["formats"])
            self.assertIsNone(data["plural"])