def test_files(self):
        temp1 = tempfile.NamedTemporaryFile()
        temp2 = tempfile.NamedTemporaryFile()

        with open(__file__, "r") as f:
            with open(__file__, "r") as g:
                self.assertEqual(get_hash(f), get_hash(g))

            self.assertNotEqual(get_hash(f), get_hash(temp1))

        self.assertEqual(get_hash(temp1), get_hash(temp1))
        self.assertNotEqual(get_hash(temp1), get_hash(temp2))