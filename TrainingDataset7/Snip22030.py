def test_file_iteration_with_text(self):
        f = File(StringIO("one\ntwo\nthree"))
        self.assertEqual(list(f), ["one\n", "two\n", "three"])