def test_with_file(self):
        prefixes = django_file_prefixes()
        self.assertIsInstance(prefixes, tuple)
        self.assertEqual(len(prefixes), 1)
        self.assertTrue(prefixes[0].endswith(f"{os.path.sep}django"))