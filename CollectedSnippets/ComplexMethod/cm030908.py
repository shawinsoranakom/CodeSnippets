def test_compound(self):
        # See gh-124285
        v = [self.No(), self.Yes(), self.Yes(), self.Yes()]
        res = v[0] and v[1] or v[2] or v[3]
        self.assertIs(res, v[2])
        self.assertEqual([e.called for e in v], [1, 0, 1, 0])

        v = [self.No(), self.No(), self.Yes(), self.Yes(), self.No()]
        res = v[0] or v[1] and v[2] or v[3] or v[4]
        self.assertIs(res, v[3])
        self.assertEqual([e.called for e in v], [1, 1, 0, 1, 0])