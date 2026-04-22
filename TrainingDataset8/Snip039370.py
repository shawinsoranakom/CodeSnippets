def test_builtins(self):
        self.assertEqual(get_hash(abs), get_hash(abs))
        self.assertNotEqual(get_hash(abs), get_hash(type))