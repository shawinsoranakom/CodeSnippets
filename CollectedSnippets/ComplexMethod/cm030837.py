def test_assignment_idiom_in_comprehensions(self):
        expected = {1: 1, 2: 4, 3: 9, 4: 16}
        actual = {j: j*j for i in range(4) for j in [i+1]}
        self.assertEqual(actual, expected)
        expected = {3: 2, 5: 6, 7: 12, 9: 20}
        actual = {j+k: j*k for i in range(4) for j in [i+1] for k in [j+1]}
        self.assertEqual(actual, expected)
        expected = {3: 2, 5: 6, 7: 12, 9: 20}
        actual = {j+k: j*k for i in range(4)  for j, k in [(i+1, i+2)]}
        self.assertEqual(actual, expected)