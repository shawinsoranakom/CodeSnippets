def test_bad_newobj_ex_args(self):
        obj = REX((copyreg.__newobj_ex__, ()))
        for proto in protocols[2:]:
            with self.subTest(proto=proto):
                with self.assertRaises((ValueError, pickle.PicklingError)) as cm:
                    self.dumps(obj, proto)
                self.assertIn(str(cm.exception), {
                    'not enough values to unpack (expected 3, got 0)',
                    '__newobj_ex__ expected 3 arguments, got 0'})
                self.assertEqual(cm.exception.__notes__, [
                    f'when serializing {REX.__module__}.REX object'])

        obj = REX((copyreg.__newobj_ex__, 42))
        for proto in protocols[2:]:
            with self.subTest(proto=proto):
                with self.assertRaises(pickle.PicklingError) as cm:
                    self.dumps(obj, proto)
                self.assertEqual(str(cm.exception),
                    'second item of the tuple returned by __reduce__ '
                    'must be a tuple, not int')
                self.assertEqual(cm.exception.__notes__, [
                    f'when serializing {REX.__module__}.REX object'])

        obj = REX((copyreg.__newobj_ex__, (REX, 42, {})))
        if self.pickler is pickle._Pickler:
            for proto in protocols[2:4]:
                with self.subTest(proto=proto):
                    with self.assertRaises(TypeError) as cm:
                        self.dumps(obj, proto)
                    self.assertEqual(str(cm.exception),
                        'Value after * must be an iterable, not int')
                    self.assertEqual(cm.exception.__notes__, [
                        f'when serializing {REX.__module__}.REX object'])
        else:
            for proto in protocols[2:]:
                with self.subTest(proto=proto):
                    with self.assertRaises(pickle.PicklingError) as cm:
                        self.dumps(obj, proto)
                    self.assertEqual(str(cm.exception),
                        'second argument to __newobj_ex__() must be a tuple, not int')
                    self.assertEqual(cm.exception.__notes__, [
                        f'when serializing {REX.__module__}.REX object'])

        obj = REX((copyreg.__newobj_ex__, (REX, (), [])))
        if self.pickler is pickle._Pickler:
            for proto in protocols[2:4]:
                with self.subTest(proto=proto):
                    with self.assertRaises(TypeError) as cm:
                        self.dumps(obj, proto)
                    self.assertEqual(str(cm.exception),
                        'Value after ** must be a mapping, not list')
                    self.assertEqual(cm.exception.__notes__, [
                        f'when serializing {REX.__module__}.REX object'])
        else:
            for proto in protocols[2:]:
                with self.subTest(proto=proto):
                    with self.assertRaises(pickle.PicklingError) as cm:
                        self.dumps(obj, proto)
                    self.assertEqual(str(cm.exception),
                        'third argument to __newobj_ex__() must be a dict, not list')
                    self.assertEqual(cm.exception.__notes__, [
                        f'when serializing {REX.__module__}.REX object'])