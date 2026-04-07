def test_outerref(self):
        inner = Company.objects.filter(point_of_contact=OuterRef("pk"))
        msg = (
            "This queryset contains a reference to an outer query and may only "
            "be used in a subquery."
        )
        with self.assertRaisesMessage(ValueError, msg):
            inner.exists()

        outer = Employee.objects.annotate(is_point_of_contact=Exists(inner))
        self.assertIs(outer.exists(), True)