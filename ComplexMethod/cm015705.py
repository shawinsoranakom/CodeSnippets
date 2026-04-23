def test_mutable_bases(self):
        # Testing mutable bases...

        # stuff that should work:
        with torch._dynamo.error_on_graph_break(False):
            class C(object):
                pass
            class C2(object):
                def __getattribute__(self, attr):
                    if attr == 'a':
                        return 2
                    else:
                        return super(C2, self).__getattribute__(attr)
                def meth(self):
                    return 1
            class D(C):
                pass
            class E(D):
                pass
        d = D()
        e = E()
        D.__bases__ = (C,)
        D.__bases__ = (C2,)
        self.assertEqual(d.meth(), 1)
        self.assertEqual(e.meth(), 1)
        self.assertEqual(d.a, 2)
        self.assertEqual(e.a, 2)
        self.assertEqual(C2.__subclasses__(), [D])

        try:
            del D.__bases__
        except (TypeError, AttributeError):
            pass
        else:
            self.fail("shouldn't be able to delete .__bases__")

        try:
            D.__bases__ = ()
        except TypeError as msg:
            if str(msg) == "a new-style class can't have only classic bases":
                self.fail("wrong error message for .__bases__ = ()")
        else:
            self.fail("shouldn't be able to set .__bases__ to ()")

        try:
            D.__bases__ = (D,)
        except TypeError:
            pass
        else:
            # actually, we'll have crashed by here...
            self.fail("shouldn't be able to create inheritance cycles")

        try:
            D.__bases__ = (C, C)
        except TypeError:
            pass
        else:
            self.fail("didn't detect repeated base classes")

        try:
            D.__bases__ = (E,)
        except TypeError:
            pass
        else:
            self.fail("shouldn't be able to create inheritance cycles")