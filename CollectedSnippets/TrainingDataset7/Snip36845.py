def test_file_extension_equality(self):
        self.assertEqual(FileExtensionValidator(), FileExtensionValidator())
        self.assertEqual(
            FileExtensionValidator(["txt"]), FileExtensionValidator(["txt"])
        )
        self.assertEqual(
            FileExtensionValidator(["TXT"]), FileExtensionValidator(["txt"])
        )
        self.assertEqual(
            FileExtensionValidator(["TXT", "png"]),
            FileExtensionValidator(["txt", "png"]),
        )
        self.assertEqual(
            FileExtensionValidator(["jpg", "png", "txt"]),
            FileExtensionValidator(["txt", "jpg", "png"]),
        )
        self.assertEqual(
            FileExtensionValidator(["txt"]),
            FileExtensionValidator(["txt"], code="invalid_extension"),
        )
        self.assertNotEqual(
            FileExtensionValidator(["txt"]), FileExtensionValidator(["png"])
        )
        self.assertNotEqual(
            FileExtensionValidator(["txt"]), FileExtensionValidator(["png", "jpg"])
        )
        self.assertNotEqual(
            FileExtensionValidator(["txt"]),
            FileExtensionValidator(["txt"], code="custom_code"),
        )
        self.assertNotEqual(
            FileExtensionValidator(["txt"]),
            FileExtensionValidator(["txt"], message="custom error message"),
        )