def test_ticket7095(self):
        # Updates that are filtered on the model being updated are somewhat
        # tricky in MySQL.
        ManagedModel.objects.create(data="mm1", tag=self.t1, public=True)
        self.assertEqual(ManagedModel.objects.update(data="mm"), 1)

        # A values() or values_list() query across joined models must use outer
        # joins appropriately.
        # Note: In Oracle, we expect a null CharField to return '' instead of
        # None.
        if connection.features.interprets_empty_strings_as_nulls:
            expected_null_charfield_repr = ""
        else:
            expected_null_charfield_repr = None
        self.assertSequenceEqual(
            Report.objects.values_list("creator__extra__info", flat=True).order_by(
                "name"
            ),
            ["e1", "e2", expected_null_charfield_repr],
        )

        # Similarly for select_related(), joins beyond an initial nullable join
        # must use outer joins so that all results are included.
        self.assertSequenceEqual(
            Report.objects.select_related("creator", "creator__extra").order_by("name"),
            [self.r1, self.r2, self.r3],
        )

        # When there are multiple paths to a table from another table, we have
        # to be careful not to accidentally reuse an inappropriate join when
        # using select_related(). We used to return the parent's Detail record
        # here by mistake.

        d1 = Detail.objects.create(data="d1")
        d2 = Detail.objects.create(data="d2")
        m1 = Member.objects.create(name="m1", details=d1)
        m2 = Member.objects.create(name="m2", details=d2)
        Child.objects.create(person=m2, parent=m1)
        obj = m1.children.select_related("person__details")[0]
        self.assertEqual(obj.person.details.data, "d2")