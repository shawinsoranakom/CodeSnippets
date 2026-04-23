def test_single_message(self):
        v = ValidationError("Not Valid")
        self.assertEqual(str(v), "['Not Valid']")
        self.assertEqual(repr(v), "ValidationError(['Not Valid'])")