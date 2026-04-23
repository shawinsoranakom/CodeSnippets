def test_simple_query(self):
        query = Query(Author)
        where = query.build_where(Q(num__gt=2))
        lookup = where.children[0]
        self.assertIsInstance(lookup, GreaterThan)
        self.assertEqual(lookup.rhs, 2)
        self.assertEqual(lookup.lhs.target, Author._meta.get_field("num"))