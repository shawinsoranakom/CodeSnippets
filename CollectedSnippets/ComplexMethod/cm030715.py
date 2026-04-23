def test_dict_constructors(self):
        # Testing dict constructor ...
        d = dict()
        self.assertEqual(d, {})
        d = dict({})
        self.assertEqual(d, {})
        d = dict({1: 2, 'a': 'b'})
        self.assertEqual(d, {1: 2, 'a': 'b'})
        self.assertEqual(d, dict(list(d.items())))
        self.assertEqual(d, dict(iter(d.items())))
        d = dict({'one':1, 'two':2})
        self.assertEqual(d, dict(one=1, two=2))
        self.assertEqual(d, dict(**d))
        self.assertEqual(d, dict({"one": 1}, two=2))
        self.assertEqual(d, dict([("two", 2)], one=1))
        self.assertEqual(d, dict([("one", 100), ("two", 200)], **d))
        self.assertEqual(d, dict(**d))

        for badarg in 0, 0, 0j, "0", [0], (0,):
            try:
                dict(badarg)
            except TypeError:
                pass
            except ValueError:
                if badarg == "0":
                    # It's a sequence, and its elements are also sequences (gotta
                    # love strings <wink>), but they aren't of length 2, so this
                    # one seemed better as a ValueError than a TypeError.
                    pass
                else:
                    self.fail("no TypeError from dict(%r)" % badarg)
            else:
                self.fail("no TypeError from dict(%r)" % badarg)

        with self.assertRaises(TypeError):
            dict({}, {})

        class Mapping:
            # Lacks a .keys() method; will be added later.
            dict = {1:2, 3:4, 'a':1j}

        try:
            dict(Mapping())
        except TypeError:
            pass
        else:
            self.fail("no TypeError from dict(incomplete mapping)")

        Mapping.keys = lambda self: list(self.dict.keys())
        Mapping.__getitem__ = lambda self, i: self.dict[i]
        d = dict(Mapping())
        self.assertEqual(d, Mapping.dict)

        # Init from sequence of iterable objects, each producing a 2-sequence.
        class AddressBookEntry:
            def __init__(self, first, last):
                self.first = first
                self.last = last
            def __iter__(self):
                return iter([self.first, self.last])

        d = dict([AddressBookEntry('Tim', 'Warsaw'),
                  AddressBookEntry('Barry', 'Peters'),
                  AddressBookEntry('Tim', 'Peters'),
                  AddressBookEntry('Barry', 'Warsaw')])
        self.assertEqual(d, {'Barry': 'Warsaw', 'Tim': 'Peters'})

        d = dict(zip(range(4), range(1, 5)))
        self.assertEqual(d, dict([(i, i+1) for i in range(4)]))

        # Bad sequence lengths.
        for bad in [('tooshort',)], [('too', 'long', 'by 1')]:
            try:
                dict(bad)
            except ValueError:
                pass
            else:
                self.fail("no ValueError from dict(%r)" % bad)