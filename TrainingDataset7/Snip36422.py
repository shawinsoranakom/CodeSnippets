def test_generator(self):
        self.assertEqual(urlencode({"a": range(2)}, doseq=True), "a=0&a=1")
        self.assertEqual(urlencode({"a": range(2)}, doseq=False), "a=range%280%2C+2%29")