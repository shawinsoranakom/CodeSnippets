def test_c_methods(self):
        if self.py_version < (3, 4):
            self.skipTest('not supported in Python < 3.4')
        c_methods = (
            # bound built-in method
            ("abcd".index, ("c",)),
            # unbound built-in method
            (str.index, ("abcd", "c")),
            # bound "slot" method
            ([1, 2, 3].__len__, ()),
            # unbound "slot" method
            (list.__len__, ([1, 2, 3],)),
            # bound "coexist" method
            ({1, 2}.__contains__, (2,)),
            # unbound "coexist" method
            (set.__contains__, ({1, 2}, 2)),
            # built-in class method
            (dict.fromkeys, (("a", 1), ("b", 2))),
            # built-in static method
            (bytearray.maketrans, (b"abc", b"xyz")),
            # subclass methods
            (Subclass([1,2,2]).count, (2,)),
            (Subclass.count, (Subclass([1,2,2]), 2)),
            (Subclass.Nested.count, (Subclass.Nested("sweet"), "e")),
        )
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            for method, args in c_methods:
                with self.subTest(proto=proto, method=method):
                    unpickled = self.loads(self.dumps(method, proto))
                    self.assertEqual(method(*args), unpickled(*args))

        # required protocol 4 in Python 3.4
        c_methods = (
            (Subclass.Nested("sweet").count, ("e",)),
        )
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            if self.py_version < (3, 5) and proto < 4:
                continue
            for method, args in c_methods:
                with self.subTest(proto=proto, method=method):
                    unpickled = self.loads(self.dumps(method, proto))
                    self.assertEqual(method(*args), unpickled(*args))

        descriptors = (
            bytearray.__dict__['maketrans'],  # built-in static method descriptor
            dict.__dict__['fromkeys'],  # built-in class method descriptor
        )
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            for descr in descriptors:
                with self.subTest(proto=proto, descr=descr):
                    self.assertRaises(TypeError, self.dumps, descr, proto)