def test_meth_class_get(self):
        # Testing __get__ method of METH_CLASS C methods...
        # Full coverage of descrobject.c::classmethod_get()

        # Baseline
        arg = [1, 2, 3]
        res = {1: None, 2: None, 3: None}
        self.assertEqual(dict.fromkeys(arg), res)
        self.assertEqual({}.fromkeys(arg), res)

        # Now get the descriptor
        descr = dict.__dict__["fromkeys"]

        # More baseline using the descriptor directly
        self.assertEqual(descr.__get__(None, dict)(arg), res)
        self.assertEqual(descr.__get__({})(arg), res)

        # Now check various error cases
        try:
            descr.__get__(None, None)
        except TypeError:
            pass
        else:
            self.fail("shouldn't have allowed descr.__get__(None, None)")
        try:
            descr.__get__(42)
        except TypeError:
            pass
        else:
            self.fail("shouldn't have allowed descr.__get__(42)")
        try:
            descr.__get__(None, 42)
        except TypeError:
            pass
        else:
            self.fail("shouldn't have allowed descr.__get__(None, 42)")
        try:
            descr.__get__(None, int)
        except TypeError:
            pass
        else:
            self.fail("shouldn't have allowed descr.__get__(None, int)")