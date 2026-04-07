def test_hash(self):
        lookup = Lookup(Value(1), Value(2))
        self.assertEqual(hash(lookup), hash(lookup))
        self.assertEqual(hash(lookup), hash(Lookup(lookup.lhs, lookup.rhs)))
        self.assertNotEqual(hash(lookup), hash(Lookup(lookup.lhs, Value(3))))
        self.assertNotEqual(hash(lookup), hash(Lookup(Value(3), lookup.rhs)))
        self.assertNotEqual(hash(lookup), hash(CustomLookup(lookup.lhs, lookup.rhs)))