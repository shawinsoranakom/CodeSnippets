def test_attribute_error(self):
        with self.assertRaises(AttributeError):
            self.a1.firstname

        with self.assertRaises(AttributeError):
            self.a1.last