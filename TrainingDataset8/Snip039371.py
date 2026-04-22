def test_regex(self):
        p2 = re.compile(".*")
        p1 = re.compile(".*")
        p3 = re.compile(".*", re.I)
        self.assertEqual(get_hash(p1), get_hash(p2))
        self.assertNotEqual(get_hash(p1), get_hash(p3))