def test_transform(self):
        query = Query(Author, alias_cols=False)
        with register_lookup(CharField, Lower):
            where = query.build_where(~Q(name__lower="foo"))
        lookup = where.children[0]
        self.assertIsInstance(lookup, Exact)
        self.assertIsInstance(lookup.lhs, Lower)
        self.assertIsInstance(lookup.lhs.lhs, Col)
        self.assertIsNone(lookup.lhs.lhs.alias)
        self.assertEqual(lookup.lhs.lhs.target, Author._meta.get_field("name"))