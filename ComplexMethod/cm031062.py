def _test_builtin_methods_have_signatures(self, cls, no_signature, unsupported_signature):
        ns = vars(cls)
        for name in ns:
            obj = getattr(cls, name, None)
            if not callable(obj) or isinstance(obj, type):
                continue
            if name not in no_signature and name not in unsupported_signature:
                with self.subTest('supported', method=name):
                    self.assertIsNotNone(inspect.signature(obj))
        for name in no_signature:
            with self.subTest('none', method=name):
                self.assertIsNone(getattr(cls, name).__text_signature__)
                self.assertRaises(ValueError, inspect.signature, getattr(cls, name))
        for name in unsupported_signature:
            with self.subTest('unsupported', method=name):
                self.assertIsNotNone(getattr(cls, name).__text_signature__)
                self.assertRaises(ValueError, inspect.signature, getattr(cls, name))