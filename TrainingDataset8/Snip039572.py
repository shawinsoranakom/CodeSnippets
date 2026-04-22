def test_file_position(self):
        with open(__file__, "r") as f:
            h1 = get_hash(f)
            self.assertEqual(h1, get_hash(f))
            f.readline()
            self.assertNotEqual(h1, get_hash(f))
            f.seek(0)
            self.assertEqual(h1, get_hash(f))