def test_reverse_assignment_deprecation(self):
        msg = (
            "Direct assignment to the reverse side of a related set is "
            "prohibited. Use article_set.set() instead."
        )
        with self.assertRaisesMessage(TypeError, msg):
            self.r2.article_set = []