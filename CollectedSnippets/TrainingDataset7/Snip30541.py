def test_multiple_fields(self):
        query = Query(Item, alias_cols=False)
        where = query.build_where(Q(modified__gt=F("created")))
        lookup = where.children[0]
        self.assertIsInstance(lookup, GreaterThan)
        self.assertIsInstance(lookup.rhs, Col)
        self.assertIsNone(lookup.rhs.alias)
        self.assertIsInstance(lookup.lhs, Col)
        self.assertIsNone(lookup.lhs.alias)
        self.assertEqual(lookup.rhs.target, Item._meta.get_field("created"))
        self.assertEqual(lookup.lhs.target, Item._meta.get_field("modified"))