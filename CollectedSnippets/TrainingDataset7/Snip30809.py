def test_subquery_exclude_outerref(self):
        qs = JobResponsibilities.objects.filter(
            Exists(Responsibility.objects.exclude(jobs=OuterRef("job"))),
        )
        self.assertTrue(qs.exists())
        self.r1.delete()
        self.assertFalse(qs.exists())