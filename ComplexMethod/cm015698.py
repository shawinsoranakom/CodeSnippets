def test_slots(self):
        # Testing __slots__...
        with torch._dynamo.error_on_graph_break(False):
            class C0(object):
                __slots__ = []
        x = C0()
        self.assertNotHasAttr(x, "__dict__")
        self.assertNotHasAttr(x, "foo")

        with torch._dynamo.error_on_graph_break(False):
            class C1(object):
                __slots__ = ['a']
        x = C1()
        self.assertNotHasAttr(x, "__dict__")
        self.assertNotHasAttr(x, "a")
        x.a = 1
        self.assertEqual(x.a, 1)
        x.a = None
        self.assertEqual(x.a, None)
        del x.a
        self.assertNotHasAttr(x, "a")

        with torch._dynamo.error_on_graph_break(False):
            class C3(object):
                __slots__ = ['a', 'b', 'c']
            x = C3()
        self.assertNotHasAttr(x, "__dict__")
        self.assertNotHasAttr(x, 'a')
        self.assertNotHasAttr(x, 'b')
        self.assertNotHasAttr(x, 'c')
        x.a = 1
        x.b = 2
        x.c = 3
        self.assertEqual(x.a, 1)
        self.assertEqual(x.b, 2)
        self.assertEqual(x.c, 3)

        with torch._dynamo.error_on_graph_break(False):
            class C4(object):
                """Validate name mangling"""
                __slots__ = ['__a']
                def __init__(self, value):
                    self.__a = value
                def get(self):
                    return self.__a
            x = C4(5)
        self.assertNotHasAttr(x, '__dict__')
        self.assertNotHasAttr(x, '__a')
        self.assertEqual(x.get(), 5)
        try:
            x.__a = 6
        except AttributeError:
            pass
        else:
            self.fail("Double underscored names not mangled")

        # Make sure slot names are proper identifiers
        try:
            with torch._dynamo.error_on_graph_break(False):
                class C(object):
                    __slots__ = [None]
        except TypeError:
            pass
        else:
            self.fail("[None] slots not caught")
        try:
            with torch._dynamo.error_on_graph_break(False):
                class C(object):
                    __slots__ = ["foo bar"]
        except TypeError:
            pass
        else:
            self.fail("['foo bar'] slots not caught")
        try:
            with torch._dynamo.error_on_graph_break(False):
                class C(object):
                    __slots__ = ["foo\0bar"]
        except TypeError:
            pass
        else:
            self.fail("['foo\\0bar'] slots not caught")
        try:
            with torch._dynamo.error_on_graph_break(False):
                class C(object):
                    __slots__ = ["1"]
        except TypeError:
            pass
        else:
            self.fail("['1'] slots not caught")
        try:
            with torch._dynamo.error_on_graph_break(False):
                class C(object):
                    __slots__ = [""]
        except TypeError:
            pass
        else:
            self.fail("[''] slots not caught")

        with torch._dynamo.error_on_graph_break(False):
            class WithValidIdentifiers(object):
                __slots__ = ["a", "a_b", "_a", "A0123456789Z"]

        # Test a single string is not expanded as a sequence.
        with torch._dynamo.error_on_graph_break(False):
            class C(object):
                __slots__ = "abc"
        c = C()
        c.abc = 5
        self.assertEqual(c.abc, 5)

        # Test unicode slot names
        # Test a single unicode string is not expanded as a sequence.
        with torch._dynamo.error_on_graph_break(False):
            class C(object):
                __slots__ = "abc"
        c = C()
        c.abc = 5
        self.assertEqual(c.abc, 5)

        # _unicode_to_string used to modify slots in certain circumstances
        slots = ("foo", "bar")
        with torch._dynamo.error_on_graph_break(False):
            class C(object):
                __slots__ = slots
        x = C()
        x.foo = 5
        self.assertEqual(x.foo, 5)
        self.assertIs(type(slots[0]), str)
        # this used to leak references
        try:
            with torch._dynamo.error_on_graph_break(False):
                class C(object):
                    __slots__ = [chr(128)]
        except (TypeError, UnicodeEncodeError):
            pass
        else:
            self.fail("[chr(128)] slots not caught")

        # Test leaks
        with torch._dynamo.error_on_graph_break(False):
            class Counted(object):
                counter = 0    # counts the number of instances alive
                def __init__(self):
                    Counted.counter += 1
                def __del__(self):
                    Counted.counter -= 1
        with torch._dynamo.error_on_graph_break(False):
            class C(object):
                __slots__ = ['a', 'b', 'c']
        x = C()
        x.a = Counted()
        x.b = Counted()
        x.c = Counted()
        self.assertEqual(Counted.counter, 3)
        del x
        support.gc_collect()
        self.assertEqual(Counted.counter, 0)
        with torch._dynamo.error_on_graph_break(False):
            class D(C):
                pass
        x = D()
        x.a = Counted()
        x.z = Counted()
        self.assertEqual(Counted.counter, 2)
        del x
        support.gc_collect()
        self.assertEqual(Counted.counter, 0)
        with torch._dynamo.error_on_graph_break(False):
            class E(D):
                __slots__ = ['e']
        x = E()
        x.a = Counted()
        x.z = Counted()
        x.e = Counted()
        self.assertEqual(Counted.counter, 3)
        del x
        support.gc_collect()
        self.assertEqual(Counted.counter, 0)

        # Test cyclical leaks [SF bug 519621]
        with torch._dynamo.error_on_graph_break(False):
            class F(object):
                __slots__ = ['a', 'b']
        s = F()
        s.a = [Counted(), s]
        self.assertEqual(Counted.counter, 1)
        s = None
        support.gc_collect()
        self.assertEqual(Counted.counter, 0)

        # Test lookup leaks [SF bug 572567]
        if hasattr(gc, 'get_objects'):
            with torch._dynamo.error_on_graph_break(False):
                class G(object):
                    def __eq__(self, other):
                        return False
            g = G()
            orig_objects = len(gc.get_objects())
            for i in range(10):
                g==g
            new_objects = len(gc.get_objects())
            self.assertEqual(orig_objects, new_objects)

        with torch._dynamo.error_on_graph_break(False):
            class H(object):
                __slots__ = ['a', 'b']
                def __init__(self):
                    self.a = 1
                    self.b = 2
                def __del__(self_):
                    self.assertEqual(self_.a, 1)
                    self.assertEqual(self_.b, 2)
        with support.captured_output('stderr') as s:
            h = H()
            del h
        self.assertEqual(s.getvalue(), '')

        with torch._dynamo.error_on_graph_break(False):
            class X(object):
                __slots__ = "a"
        with self.assertRaises(AttributeError):
            del X().a

        # Inherit from object on purpose to check some backwards compatibility paths
        with torch._dynamo.error_on_graph_break(False):
            class X(object):
                __slots__ = "a"
        with self.assertRaisesRegex(AttributeError, "'test.test_descr.ClassPropertiesAndMethods.test_slots.<locals>.X' object has no attribute 'a'"):
            X().a

        # Test string subclass in `__slots__`, see gh-98783
        with torch._dynamo.error_on_graph_break(False):
            class SubStr(str):
                pass
        with torch._dynamo.error_on_graph_break(False):
            class X(object):
                __slots__ = (SubStr('x'),)
        X().x = 1
        with self.assertRaisesRegex(AttributeError, "'X' object has no attribute 'a'"):
            X().a