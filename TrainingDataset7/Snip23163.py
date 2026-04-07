def test_pretty_name(self):
        self.assertEqual(pretty_name("john_doe"), "John doe")
        self.assertEqual(pretty_name(None), "")
        self.assertEqual(pretty_name(""), "")