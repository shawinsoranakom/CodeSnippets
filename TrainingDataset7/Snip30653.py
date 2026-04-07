def test_ticket14876(self):
        # Note: when combining the query we need to have information available
        # about the join type of the trimmed "creator__isnull" join. If we
        # don't have that information, then the join is created as INNER JOIN
        # and results will be incorrect.
        q1 = Report.objects.filter(
            Q(creator__isnull=True) | Q(creator__extra__info="e1")
        )
        q2 = Report.objects.filter(Q(creator__isnull=True)) | Report.objects.filter(
            Q(creator__extra__info="e1")
        )
        self.assertCountEqual(q1, [self.r1, self.r3])
        self.assertEqual(str(q1.query), str(q2.query))

        q1 = Report.objects.filter(
            Q(creator__extra__info="e1") | Q(creator__isnull=True)
        )
        q2 = Report.objects.filter(
            Q(creator__extra__info="e1")
        ) | Report.objects.filter(Q(creator__isnull=True))
        self.assertCountEqual(q1, [self.r1, self.r3])
        self.assertEqual(str(q1.query), str(q2.query))

        q1 = Item.objects.filter(
            Q(creator=self.a1) | Q(creator__report__name="r1")
        ).order_by()
        q2 = (
            Item.objects.filter(Q(creator=self.a1)).order_by()
            | Item.objects.filter(Q(creator__report__name="r1")).order_by()
        )
        self.assertCountEqual(q1, [self.i1])
        self.assertEqual(str(q1.query), str(q2.query))

        q1 = Item.objects.filter(
            Q(creator__report__name="e1") | Q(creator=self.a1)
        ).order_by()
        q2 = (
            Item.objects.filter(Q(creator__report__name="e1")).order_by()
            | Item.objects.filter(Q(creator=self.a1)).order_by()
        )
        self.assertCountEqual(q1, [self.i1])
        self.assertEqual(str(q1.query), str(q2.query))