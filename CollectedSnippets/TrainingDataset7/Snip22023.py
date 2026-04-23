def test_file_iteration(self):
        """
        File objects should yield lines when iterated over.
        Refs #22107.
        """
        file = File(BytesIO(b"one\ntwo\nthree"))
        self.assertEqual(list(file), [b"one\n", b"two\n", b"three"])