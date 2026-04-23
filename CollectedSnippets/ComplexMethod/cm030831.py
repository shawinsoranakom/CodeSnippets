def test_py_methods(self):
        if self.py_version < (3, 4):
            self.skipTest('not supported in Python < 3.4')
        py_methods = (
            PyMethodsTest.wine,
            PyMethodsTest().biscuits,
        )
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            for method in py_methods:
                with self.subTest(proto=proto, method=method):
                    unpickled = self.loads(self.dumps(method, proto))
                    self.assertEqual(method(), unpickled())

        # required protocol 4 in Python 3.4
        py_methods = (
            PyMethodsTest.cheese,
            PyMethodsTest.Nested.ketchup,
            PyMethodsTest.Nested.maple,
            PyMethodsTest.Nested().pie
        )
        py_unbound_methods = (
            (PyMethodsTest.biscuits, PyMethodsTest),
            (PyMethodsTest.Nested.pie, PyMethodsTest.Nested)
        )
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            if self.py_version < (3, 5) and proto < 4:
                continue
            for method in py_methods:
                with self.subTest(proto=proto, method=method):
                    unpickled = self.loads(self.dumps(method, proto))
                    self.assertEqual(method(), unpickled())
            for method, cls in py_unbound_methods:
                obj = cls()
                with self.subTest(proto=proto, method=method):
                    unpickled = self.loads(self.dumps(method, proto))
                    self.assertEqual(method(obj), unpickled(obj))

        descriptors = (
            PyMethodsTest.__dict__['cheese'],  # static method descriptor
            PyMethodsTest.__dict__['wine'],  # class method descriptor
        )
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            for descr in descriptors:
                with self.subTest(proto=proto, descr=descr):
                    self.assertRaises(TypeError, self.dumps, descr, proto)