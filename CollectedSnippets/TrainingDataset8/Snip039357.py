def test_string(self):
        self.assertEqual(get_hash("hello"), get_hash("hello"))
        self.assertNotEqual(get_hash("hello"), get_hash("hellö"))