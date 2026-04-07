def test_m2o_recursive2(self):
        self.assertEqual(self.kid.mother.id, self.mom.id)
        self.assertEqual(self.kid.father.id, self.dad.id)
        self.assertSequenceEqual(self.dad.fathers_child_set.all(), [self.kid])
        self.assertSequenceEqual(self.mom.mothers_child_set.all(), [self.kid])
        self.assertSequenceEqual(self.kid.mothers_child_set.all(), [])
        self.assertSequenceEqual(self.kid.fathers_child_set.all(), [])