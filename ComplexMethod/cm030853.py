def test_pickle(self):
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            for fd in (
                frozendict(),
                frozendict(x=1, y=2),
                FrozenDict(x=1, y=2),
                FrozenDictSlots(x=1, y=2),
            ):
                if type(fd) == FrozenDict:
                    fd.attr = 123
                if type(fd) == FrozenDictSlots:
                    fd.slot_attr = 456
                with self.subTest(fd=fd, proto=proto):
                    if proto >= 2:
                        p = pickle.dumps(fd, proto)
                        fd2 = pickle.loads(p)
                        self.assertEqual(fd2, fd)
                        self.assertEqual(type(fd2), type(fd))
                        if type(fd) == FrozenDict:
                            self.assertEqual(fd2.attr, 123)
                        if type(fd) == FrozenDictSlots:
                            self.assertEqual(fd2.slot_attr, 456)
                    else:
                        # protocol 0 and 1 don't support frozendict
                        with self.assertRaises(TypeError):
                            pickle.dumps(fd, proto)