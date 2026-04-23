def test_malformed_slug_raises_error(self):
        mtv = ModelToValidate(number=10, name="Some Name", slug="##invalid##")
        self.assertFailsValidation(mtv.full_clean, ["slug"])