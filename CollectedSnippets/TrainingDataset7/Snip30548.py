def test_iterable_lookup_value(self):
        query = Query(Item)
        where = query.build_where(Q(name=["a", "b"]))
        name_exact = where.children[0]
        self.assertIsInstance(name_exact, Exact)
        self.assertEqual(name_exact.rhs, "['a', 'b']")