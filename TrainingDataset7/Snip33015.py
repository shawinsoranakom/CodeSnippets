def test_ljust(self):
        self.assertEqual(ljust("test", 10), "test      ")
        self.assertEqual(ljust("test", 3), "test")