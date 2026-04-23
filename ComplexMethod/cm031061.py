def _test_module_has_signatures(self, module,
                no_signature=(), unsupported_signature=(),
                methods_no_signature={}, methods_unsupported_signature={},
                good_exceptions=()):
        # This checks all builtin callables in CPython have signatures
        # A few have signatures Signature can't yet handle, so we skip those
        # since they will have to wait until PEP 457 adds the required
        # introspection support to the inspect module
        # Some others also haven't been converted yet for various other
        # reasons, so we also skip those for the time being, but design
        # the test to fail in order to indicate when it needs to be
        # updated.
        no_signature = no_signature or set()
        # Check the signatures we expect to be there
        ns = vars(module)
        try:
            names = set(module.__all__)
        except AttributeError:
            names = set(name for name in ns if self.is_public(name))
        for name, obj in sorted(ns.items()):
            if name not in names:
                continue
            if not callable(obj):
                continue
            if (isinstance(obj, type) and
                issubclass(obj, BaseException) and
                name not in good_exceptions):
                no_signature.add(name)
            if name not in no_signature and name not in unsupported_signature:
                with self.subTest('supported', builtin=name):
                    self.assertIsNotNone(inspect.signature(obj))
            if isinstance(obj, type):
                with self.subTest(type=name):
                    self._test_builtin_methods_have_signatures(obj,
                            methods_no_signature.get(name, ()),
                            methods_unsupported_signature.get(name, ()))
        # Check callables that haven't been converted don't claim a signature
        # This ensures this test will start failing as more signatures are
        # added, so the affected items can be moved into the scope of the
        # regression test above
        for name in no_signature:
            with self.subTest('none', builtin=name):
                obj = ns[name]
                self.assertIsNone(obj.__text_signature__)
                self.assertRaises(ValueError, inspect.signature, obj)
        for name in unsupported_signature:
            with self.subTest('unsupported', builtin=name):
                obj = ns[name]
                self.assertIsNotNone(obj.__text_signature__)
                self.assertRaises(ValueError, inspect.signature, obj)