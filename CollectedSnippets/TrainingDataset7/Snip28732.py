def test_issue_7105(self):
        # Regressions tests for #7105: dates() queries should be able to use
        # fields from the parent model as easily as the child.
        Child.objects.create(
            name="child", created=datetime.datetime(2008, 6, 26, 17, 0, 0)
        )
        datetimes = list(Child.objects.datetimes("created", "month"))
        self.assertEqual(datetimes, [datetime.datetime(2008, 6, 1, 0, 0)])