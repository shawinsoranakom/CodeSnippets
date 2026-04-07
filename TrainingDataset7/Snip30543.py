def test_negated_nullable(self):
        query = Query(Item)
        where = query.build_where(~Q(modified__lt=datetime(2017, 1, 1)))
        self.assertTrue(where.negated)
        lookup = where.children[0]
        self.assertIsInstance(lookup, LessThan)
        self.assertEqual(lookup.lhs.target, Item._meta.get_field("modified"))
        lookup = where.children[1]
        self.assertIsInstance(lookup, IsNull)
        self.assertEqual(lookup.lhs.target, Item._meta.get_field("modified"))