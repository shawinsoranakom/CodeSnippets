def test_basics(self):
        TE = self.MainEnum
        if self.is_flag:
            self.assertEqual(repr(TE), "<flag 'MainEnum'>")
            self.assertEqual(str(TE), "<flag 'MainEnum'>")
            self.assertEqual(format(TE), "<flag 'MainEnum'>")
            self.assertTrue(TE(5) is self.dupe2)
            self.assertTrue(7 in TE)
        else:
            self.assertEqual(repr(TE), "<enum 'MainEnum'>")
            self.assertEqual(str(TE), "<enum 'MainEnum'>")
            self.assertEqual(format(TE), "<enum 'MainEnum'>")
        self.assertEqual(list(TE), [TE.first, TE.second, TE.third])
        self.assertEqual(
                [m.name for m in TE],
                self.names,
                )
        self.assertEqual(
                [m.value for m in TE],
                self.values,
                )
        self.assertEqual(
                [m.first for m in TE],
                ['first is first!', 'second is first!', 'third is first!']
                )
        for member, name in zip(TE, self.names, strict=True):
            self.assertIs(TE[name], member)
        for member, value in zip(TE, self.values, strict=True):
            self.assertIs(TE(value), member)
        if issubclass(TE, StrEnum):
            self.assertTrue(TE.dupe is TE('third') is TE['dupe'])
        elif TE._member_type_ is str:
            self.assertTrue(TE.dupe is TE('3') is TE['dupe'])
        elif issubclass(TE, Flag):
            self.assertTrue(TE.dupe is TE(3) is TE['dupe'])
        else:
            self.assertTrue(TE.dupe is TE(self.values[2]) is TE['dupe'])