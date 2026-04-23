def test_create_helper(self):
        items = [("a", 1), ("b", 2), ("c", 3)]
        for connector in [Q.AND, Q.OR, Q.XOR]:
            with self.subTest(connector=connector):
                self.assertEqual(
                    Q.create(items, connector=connector),
                    Q(*items, _connector=connector),
                )