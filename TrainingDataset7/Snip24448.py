def test02_setslice(self):
        "Slice assignment"

        def setfcn(x, i, j, k, L):
            x[i:j:k] = range(L)

        pl, ul = self.lists_of_len()
        for slen in range(self.limit + 1):
            ssl = nextRange(slen)
            with self.subTest(slen=slen):
                ul[:] = ssl
                pl[:] = ssl
                self.assertEqual(pl, ul[:], "set slice [:]")

                for i in self.limits_plus(1):
                    ssl = nextRange(slen)
                    ul[i:] = ssl
                    pl[i:] = ssl
                    self.assertEqual(pl, ul[:], "set slice [%d:]" % (i))

                    ssl = nextRange(slen)
                    ul[:i] = ssl
                    pl[:i] = ssl
                    self.assertEqual(pl, ul[:], "set slice [:%d]" % (i))

                    for j in self.limits_plus(1):
                        ssl = nextRange(slen)
                        ul[i:j] = ssl
                        pl[i:j] = ssl
                        self.assertEqual(pl, ul[:], "set slice [%d:%d]" % (i, j))

                        for k in self.step_range():
                            ssl = nextRange(len(ul[i:j:k]))
                            ul[i:j:k] = ssl
                            pl[i:j:k] = ssl
                            self.assertEqual(
                                pl, ul[:], "set slice [%d:%d:%d]" % (i, j, k)
                            )

                            sliceLen = len(ul[i:j:k])
                            msg = (
                                f"attempt to assign sequence of size {sliceLen + 1} "
                                f"to extended slice of size {sliceLen}"
                            )
                            with self.assertRaisesMessage(ValueError, msg):
                                setfcn(ul, i, j, k, sliceLen + 1)
                            if sliceLen > 2:
                                msg = (
                                    f"attempt to assign sequence of size {sliceLen - 1}"
                                    f" to extended slice of size {sliceLen}"
                                )
                                with self.assertRaisesMessage(ValueError, msg):
                                    setfcn(ul, i, j, k, sliceLen - 1)

                    for k in self.step_range():
                        ssl = nextRange(len(ul[i::k]))
                        ul[i::k] = ssl
                        pl[i::k] = ssl
                        self.assertEqual(pl, ul[:], "set slice [%d::%d]" % (i, k))

                        ssl = nextRange(len(ul[:i:k]))
                        ul[:i:k] = ssl
                        pl[:i:k] = ssl
                        self.assertEqual(pl, ul[:], "set slice [:%d:%d]" % (i, k))

                for k in self.step_range():
                    ssl = nextRange(len(ul[::k]))
                    ul[::k] = ssl
                    pl[::k] = ssl
                    self.assertEqual(pl, ul[:], "set slice [::%d]" % (k))