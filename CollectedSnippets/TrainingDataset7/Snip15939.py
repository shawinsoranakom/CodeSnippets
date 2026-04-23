def _check(self, target):
        self.assertEqual(self.n.nested(lambda obj: obj.num), target)