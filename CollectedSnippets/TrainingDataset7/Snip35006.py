def dummy_test(self):
        """
        A dummy test for testing subTest failures.
        """
        for i in range(3):
            with self.subTest(index=i):
                self.assertEqual(i, 1)