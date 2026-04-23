def test_properties(self):
        # Testing property...
        with torch._dynamo.error_on_graph_break(False):
            class C(object):
                def getx(self):
                    return self.__x
                def setx(self, value):
                    self.__x = value
                def delx(self):
                    del self.__x
                x = property(getx, setx, delx, doc="I'm the x property.")
        a = C()
        self.assertNotHasAttr(a, "x")
        a.x = 42
        self.assertEqual(a._C__x, 42)
        self.assertEqual(a.x, 42)
        del a.x
        self.assertNotHasAttr(a, "x")
        self.assertNotHasAttr(a, "_C__x")
        C.x.__set__(a, 100)
        self.assertEqual(C.x.__get__(a), 100)
        C.x.__delete__(a)
        self.assertNotHasAttr(a, "x")

        raw = C.__dict__['x']
        self.assertIsInstance(raw, property)

        attrs = dir(raw)
        self.assertIn("__doc__", attrs)
        self.assertIn("fget", attrs)
        self.assertIn("fset", attrs)
        self.assertIn("fdel", attrs)

        self.assertEqual(raw.__doc__, "I'm the x property.")
        self.assertIs(raw.fget, C.__dict__['getx'])
        self.assertIs(raw.fset, C.__dict__['setx'])
        self.assertIs(raw.fdel, C.__dict__['delx'])

        for attr in "fget", "fset", "fdel":
            try:
                setattr(raw, attr, 42)
            except AttributeError as msg:
                if str(msg).find('readonly') < 0:
                    self.fail("when setting readonly attr %r on a property, "
                              "got unexpected AttributeError msg %r" % (attr, str(msg)))
            else:
                self.fail("expected AttributeError from trying to set readonly %r "
                          "attr on a property" % attr)

        raw.__doc__ = 42
        self.assertEqual(raw.__doc__, 42)

        with torch._dynamo.error_on_graph_break(False):
            class D(object):
                __getitem__ = property(lambda s: 1/0)

        d = D()
        try:
            for i in d:
                str(i)
        except ZeroDivisionError:
            pass
        else:
            self.fail("expected ZeroDivisionError from bad property")