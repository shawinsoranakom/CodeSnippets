def test_get_version_tuple(self):
        self.assertEqual(get_version_tuple("1.2.3"), (1, 2, 3))
        self.assertEqual(get_version_tuple("1.2.3b2"), (1, 2, 3))
        self.assertEqual(get_version_tuple("1.2.3b2.dev0"), (1, 2, 3))