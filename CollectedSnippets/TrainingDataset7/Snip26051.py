def test_m2o_recursive(self):
        self.assertSequenceEqual(self.r.child_set.all(), [self.c])
        self.assertEqual(self.r.child_set.get(name__startswith="Child").id, self.c.id)
        self.assertIsNone(self.r.parent)
        self.assertSequenceEqual(self.c.child_set.all(), [])
        self.assertEqual(self.c.parent.id, self.r.id)