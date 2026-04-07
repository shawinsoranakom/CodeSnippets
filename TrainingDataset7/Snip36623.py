def test_escape(self):
        pattern = r"\\\^\$\.\|\?\*\+\(\)\["
        expected = [("\\^$.|?*+()[", [])]
        result = regex_helper.normalize(pattern)
        self.assertEqual(result, expected)