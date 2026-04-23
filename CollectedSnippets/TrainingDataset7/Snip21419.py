def test_not_equal_Value(self):
        f = F("name")
        value = Value("name")
        self.assertNotEqual(f, value)
        self.assertNotEqual(value, f)