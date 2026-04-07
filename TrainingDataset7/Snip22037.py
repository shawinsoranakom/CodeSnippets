def test_open_supports_full_signature(self):
        called = False

        def opener(path, flags):
            nonlocal called
            called = True
            return os.open(path, flags)

        file_path = Path(__file__).parent / "test.png"
        with open(file_path) as f:
            test_file = File(f)

        with test_file.open(opener=opener):
            self.assertIs(called, True)