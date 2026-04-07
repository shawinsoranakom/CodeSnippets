def test_managers(self):
        a1 = Child1.objects.create(name="fred", data="a1")
        a2 = Child1.objects.create(name="barney", data="a2")
        b1 = Child2.objects.create(name="fred", data="b1", value=1)
        b2 = Child2.objects.create(name="barney", data="b2", value=42)
        c1 = Child3.objects.create(name="fred", data="c1", comment="yes")
        c2 = Child3.objects.create(name="barney", data="c2", comment="no")
        d1 = Child4.objects.create(name="fred", data="d1")
        d2 = Child4.objects.create(name="barney", data="d2")
        fred1 = Child5.objects.create(name="fred", comment="yes")
        Child5.objects.create(name="barney", comment="no")
        f1 = Child6.objects.create(name="fred", data="f1", value=42)
        f2 = Child6.objects.create(name="barney", data="f2", value=42)
        fred2 = Child7.objects.create(name="fred")
        barney = Child7.objects.create(name="barney")

        self.assertSequenceEqual(Child1.manager1.all(), [a1])
        self.assertSequenceEqual(Child1.manager2.all(), [a2])
        self.assertSequenceEqual(Child1._default_manager.all(), [a1])

        self.assertSequenceEqual(Child2._default_manager.all(), [b1])
        self.assertSequenceEqual(Child2.restricted.all(), [b2])

        self.assertSequenceEqual(Child3._default_manager.all(), [c1])
        self.assertSequenceEqual(Child3.manager1.all(), [c1])
        self.assertSequenceEqual(Child3.manager2.all(), [c2])

        # Since Child6 inherits from Child4, the corresponding rows from f1 and
        # f2 also appear here. This is the expected result.
        self.assertSequenceEqual(
            Child4._default_manager.order_by("data"),
            [d1, d2, f1.child4_ptr, f2.child4_ptr],
        )
        self.assertCountEqual(Child4.manager1.all(), [d1, f1.child4_ptr])
        self.assertCountEqual(Child5._default_manager.all(), [fred1])
        self.assertCountEqual(Child6._default_manager.all(), [f1, f2])
        self.assertSequenceEqual(
            Child7._default_manager.order_by("name"),
            [barney, fred2],
        )