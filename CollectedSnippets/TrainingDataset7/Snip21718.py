def test_regression_7314_7372(self):
        """
        Regression tests for #7314 and #7372
        """
        rm = RevisionableModel.objects.create(
            title="First Revision", when=datetime.datetime(2008, 9, 28, 10, 30, 0)
        )
        self.assertEqual(rm.pk, rm.base.pk)

        rm2 = rm.new_revision()
        rm2.title = "Second Revision"
        rm.when = datetime.datetime(2008, 9, 28, 14, 25, 0)
        rm2.save()

        self.assertEqual(rm2.title, "Second Revision")
        self.assertEqual(rm2.base.title, "First Revision")

        self.assertNotEqual(rm2.pk, rm.pk)
        self.assertEqual(rm2.base.pk, rm.pk)

        # Queryset to match most recent revision:
        qs = RevisionableModel.objects.extra(
            where=[
                "%(table)s.id IN "
                "(SELECT MAX(rev.id) FROM %(table)s rev GROUP BY rev.base_id)"
                % {
                    "table": RevisionableModel._meta.db_table,
                }
            ]
        )

        self.assertQuerySetEqual(
            qs,
            [("Second Revision", "First Revision")],
            transform=lambda r: (r.title, r.base.title),
        )

        # Queryset to search for string in title:
        qs2 = RevisionableModel.objects.filter(title__contains="Revision")
        self.assertQuerySetEqual(
            qs2,
            [
                ("First Revision", "First Revision"),
                ("Second Revision", "First Revision"),
            ],
            transform=lambda r: (r.title, r.base.title),
            ordered=False,
        )

        # Following queryset should return the most recent revision:
        self.assertQuerySetEqual(
            qs & qs2,
            [("Second Revision", "First Revision")],
            transform=lambda r: (r.title, r.base.title),
            ordered=False,
        )