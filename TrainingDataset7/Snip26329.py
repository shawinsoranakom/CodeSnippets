def test_assign_forward(self):
        msg = (
            "Direct assignment to the reverse side of a many-to-many set is "
            "prohibited. Use article_set.set() instead."
        )
        with self.assertRaisesMessage(TypeError, msg):
            self.p2.article_set = [self.a4, self.a3]