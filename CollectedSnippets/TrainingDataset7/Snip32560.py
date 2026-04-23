def test_string_form_referencing(self):
        """
        Regression test for #1661 and #1662

        String form referencing of models works, both as pre and post
        reference, on all RelatedField types.
        """

        f1 = Foo(name="Foo1")
        f1.save()
        f2 = Foo(name="Foo2")
        f2.save()

        w1 = Whiz(name="Whiz1")
        w1.save()

        b1 = Bar(name="Bar1", normal=f1, fwd=w1, back=f2)
        b1.save()

        self.assertEqual(b1.normal, f1)

        self.assertEqual(b1.fwd, w1)

        self.assertEqual(b1.back, f2)

        base1 = Base(name="Base1")
        base1.save()

        child1 = Child(name="Child1", parent=base1)
        child1.save()

        self.assertEqual(child1.parent, base1)