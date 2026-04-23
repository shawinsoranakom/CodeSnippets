def test_supers(self):
        # Testing super...

        class A(object):
            def meth(self, a):
                return "A(%r)" % a

        self.assertEqual(A().meth(1), "A(1)")

        class B(A):
            def __init__(self):
                self.__super = super(B, self)
            def meth(self, a):
                return "B(%r)" % a + self.__super.meth(a)

        self.assertEqual(B().meth(2), "B(2)A(2)")

        class C(A):
            def meth(self, a):
                return "C(%r)" % a + self.__super.meth(a)
        C._C__super = super(C)

        self.assertEqual(C().meth(3), "C(3)A(3)")

        class D(C, B):
            def meth(self, a):
                return "D(%r)" % a + super(D, self).meth(a)

        self.assertEqual(D().meth(4), "D(4)C(4)B(4)A(4)")

        # Test for subclassing super

        class mysuper(super):
            def __init__(self, *args):
                return super(mysuper, self).__init__(*args)

        class E(D):
            def meth(self, a):
                return "E(%r)" % a + mysuper(E, self).meth(a)

        self.assertEqual(E().meth(5), "E(5)D(5)C(5)B(5)A(5)")

        class F(E):
            def meth(self, a):
                s = self.__super # == mysuper(F, self)
                return "F(%r)[%s]" % (a, s.__class__.__name__) + s.meth(a)
        F._F__super = mysuper(F)

        self.assertEqual(F().meth(6), "F(6)[mysuper]E(6)D(6)C(6)B(6)A(6)")

        # Make sure certain errors are raised

        try:
            super(D, 42)
        except TypeError:
            pass
        else:
            self.fail("shouldn't allow super(D, 42)")

        try:
            super(D, C())
        except TypeError:
            pass
        else:
            self.fail("shouldn't allow super(D, C())")

        try:
            super(D).__get__(12)
        except TypeError:
            pass
        else:
            self.fail("shouldn't allow super(D).__get__(12)")

        try:
            super(D).__get__(C())
        except TypeError:
            pass
        else:
            self.fail("shouldn't allow super(D).__get__(C())")

        # Make sure data descriptors can be overridden and accessed via super
        # (new feature in Python 2.3)

        class DDbase(object):
            def getx(self): return 42
            x = property(getx)

        class DDsub(DDbase):
            def getx(self): return "hello"
            x = property(getx)

        dd = DDsub()
        self.assertEqual(dd.x, "hello")
        self.assertEqual(super(DDsub, dd).x, 42)

        # Ensure that super() lookup of descriptor from classmethod
        # works (SF ID# 743627)

        class Base(object):
            aProp = property(lambda self: "foo")

        class Sub(Base):
            @classmethod
            def test(klass):
                return super(Sub,klass).aProp

        self.assertEqual(Sub.test(), Base.aProp)

        # Verify that super() doesn't allow keyword args
        with self.assertRaises(TypeError):
            super(Base, kw=1)