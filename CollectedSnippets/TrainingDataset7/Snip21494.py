def test_equal(self):
        value = Value("name")
        self.assertEqual(value, Value("name"))
        self.assertNotEqual(value, Value("username"))