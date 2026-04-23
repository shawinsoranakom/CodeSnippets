def test_tickets_2874_3002(self):
        qs = Item.objects.select_related().order_by("note__note", "name")
        self.assertQuerySetEqual(qs, [self.i2, self.i4, self.i1, self.i3])

        # This is also a good select_related() test because there are multiple
        # Note entries in the SQL. The two Note items should be different.
        self.assertEqual(repr(qs[0].note), "<Note: n2>")
        self.assertEqual(repr(qs[0].creator.extra.note), "<Note: n1>")