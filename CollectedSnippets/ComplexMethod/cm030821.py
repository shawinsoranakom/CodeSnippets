def _test_recursive_collection_and_inst(self, factory, oldminproto=None,
                                            minprotocol=0):
        if self.py_version < (3, 0):
            self.skipTest('"classic" classes are not interoperable with Python 2')
        # Mutable object containing a collection containing the original
        # object.
        protocols = range(minprotocol, pickle.HIGHEST_PROTOCOL + 1)
        o = Object()
        o.attr = factory([o])
        t = type(o.attr)
        with self.subTest('obj -> {t.__name__} -> obj'):
            for proto in protocols:
                with self.subTest(proto=proto):
                    s = self.dumps(o, proto)
                    x = self.loads(s)
                    self.assertIsInstance(x.attr, t)
                    self.assertEqual(len(x.attr), 1)
                    self.assertIsInstance(list(x.attr)[0], Object)
                    self.assertIs(list(x.attr)[0], x)

        # Collection containing a mutable object containing the original
        # collection.
        o = o.attr
        with self.subTest(f'{t.__name__} -> obj -> {t.__name__}'):
            if self.py_version < (3, 4) and oldminproto is None:
                self.skipTest('not supported in Python < 3.4')
            for proto in protocols:
                with self.subTest(proto=proto):
                    if self.py_version < (3, 4) and proto < oldminproto:
                        self.skipTest(f'requires protocol {oldminproto} in Python < 3.4')
                    s = self.dumps(o, proto)
                    x = self.loads(s)
                    self.assertIsInstance(x, t)
                    self.assertEqual(len(x), 1)
                    self.assertIsInstance(list(x)[0], Object)
                    self.assertIs(list(x)[0].attr, x)