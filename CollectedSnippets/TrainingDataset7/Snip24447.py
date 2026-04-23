def test01_getslice(self):
        "Slice retrieval"
        pl, ul = self.lists_of_len()
        for i in self.limits_plus(1):
            with self.subTest(i=i):
                self.assertEqual(pl[i:], ul[i:], "slice [%d:]" % (i))
                self.assertEqual(pl[:i], ul[:i], "slice [:%d]" % (i))

                for j in self.limits_plus(1):
                    self.assertEqual(pl[i:j], ul[i:j], "slice [%d:%d]" % (i, j))
                    for k in self.step_range():
                        self.assertEqual(
                            pl[i:j:k], ul[i:j:k], "slice [%d:%d:%d]" % (i, j, k)
                        )

                for k in self.step_range():
                    self.assertEqual(pl[i::k], ul[i::k], "slice [%d::%d]" % (i, k))
                    self.assertEqual(pl[:i:k], ul[:i:k], "slice [:%d:%d]" % (i, k))

        for k in self.step_range():
            with self.subTest(k=k):
                self.assertEqual(pl[::k], ul[::k], "slice [::%d]" % (k))