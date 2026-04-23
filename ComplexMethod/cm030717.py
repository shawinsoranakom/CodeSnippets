def test_set_class(self):
        # Testing __class__ assignment...
        class C(object): pass
        class D(object): pass
        class E(object): pass
        class F(D, E): pass
        for cls in C, D, E, F:
            for cls2 in C, D, E, F:
                x = cls()
                x.__class__ = cls2
                self.assertIs(x.__class__, cls2)
                x.__class__ = cls
                self.assertIs(x.__class__, cls)
        def cant(x, C):
            try:
                x.__class__ = C
            except TypeError:
                pass
            else:
                self.fail("shouldn't allow %r.__class__ = %r" % (x, C))
            try:
                delattr(x, "__class__")
            except (TypeError, AttributeError):
                pass
            else:
                self.fail("shouldn't allow del %r.__class__" % x)
        cant(C(), list)
        cant(list(), C)
        cant(C(), 1)
        cant(C(), object)
        cant(object(), list)
        cant(list(), object)
        class Int(int): __slots__ = []
        cant(True, int)
        cant(2, bool)
        o = object()
        cant(o, int)
        cant(o, type(None))
        del o
        class G(object):
            __slots__ = ["a", "b"]
        class H(object):
            __slots__ = ["b", "a"]
        class I(object):
            __slots__ = ["a", "b"]
        class J(object):
            __slots__ = ["c", "b"]
        class K(object):
            __slots__ = ["a", "b", "d"]
        class L(H):
            __slots__ = ["e"]
        class M(I):
            __slots__ = ["e"]
        class N(J):
            __slots__ = ["__weakref__"]
        class P(J):
            __slots__ = ["__dict__"]
        class Q(J):
            pass
        class R(J):
            __slots__ = ["__dict__", "__weakref__"]

        for cls, cls2 in ((G, H), (G, I), (I, H), (Q, R), (R, Q)):
            x = cls()
            x.a = 1
            x.__class__ = cls2
            self.assertIs(x.__class__, cls2,
                   "assigning %r as __class__ for %r silently failed" % (cls2, x))
            self.assertEqual(x.a, 1)
            x.__class__ = cls
            self.assertIs(x.__class__, cls,
                   "assigning %r as __class__ for %r silently failed" % (cls, x))
            self.assertEqual(x.a, 1)
        for cls in G, J, K, L, M, N, P, R, list, Int:
            for cls2 in G, J, K, L, M, N, P, R, list, Int:
                if cls is cls2:
                    continue
                cant(cls(), cls2)

        # Issue5283: when __class__ changes in __del__, the wrong
        # type gets DECREF'd.
        class O(object):
            pass
        class A(object):
            def __del__(self):
                self.__class__ = O
        l = [A() for x in range(100)]
        del l