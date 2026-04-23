def test_assign_reverse(self):
        msg = (
            "Direct assignment to the forward side of a many-to-many "
            "set is prohibited. Use publications.set() instead."
        )
        with self.assertRaisesMessage(TypeError, msg):
            self.a1.publications = [self.p1, self.p2]