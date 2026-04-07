def test03_delslice(self):
        "Delete slice"
        for Len in range(self.limit):
            pl, ul = self.lists_of_len(Len)
            with self.subTest(Len=Len):
                del pl[:]
                del ul[:]
                self.assertEqual(pl[:], ul[:], "del slice [:]")
                for i in range(-Len - 1, Len + 1):
                    pl, ul = self.lists_of_len(Len)
                    del pl[i:]
                    del ul[i:]
                    self.assertEqual(pl[:], ul[:], "del slice [%d:]" % (i))
                    pl, ul = self.lists_of_len(Len)
                    del pl[:i]
                    del ul[:i]
                    self.assertEqual(pl[:], ul[:], "del slice [:%d]" % (i))
                    for j in range(-Len - 1, Len + 1):
                        pl, ul = self.lists_of_len(Len)
                        del pl[i:j]
                        del ul[i:j]
                        self.assertEqual(pl[:], ul[:], "del slice [%d:%d]" % (i, j))
                        for k in [*range(-Len - 1, 0), *range(1, Len)]:
                            pl, ul = self.lists_of_len(Len)
                            del pl[i:j:k]
                            del ul[i:j:k]
                            self.assertEqual(
                                pl[:], ul[:], "del slice [%d:%d:%d]" % (i, j, k)
                            )

                    for k in [*range(-Len - 1, 0), *range(1, Len)]:
                        pl, ul = self.lists_of_len(Len)
                        del pl[:i:k]
                        del ul[:i:k]
                        self.assertEqual(pl[:], ul[:], "del slice [:%d:%d]" % (i, k))

                        pl, ul = self.lists_of_len(Len)
                        del pl[i::k]
                        del ul[i::k]
                        self.assertEqual(pl[:], ul[:], "del slice [%d::%d]" % (i, k))

                for k in [*range(-Len - 1, 0), *range(1, Len)]:
                    pl, ul = self.lists_of_len(Len)
                    del pl[::k]
                    del ul[::k]
                    self.assertEqual(pl[:], ul[:], "del slice [::%d]" % (k))