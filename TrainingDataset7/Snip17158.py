def test_existing_join_not_promoted(self):
        # No promotion for existing joins
        qs = Charlie.objects.filter(alfa__name__isnull=False).annotate(
            Count("alfa__name")
        )
        self.assertIn(" INNER JOIN ", str(qs.query))
        # Also, the existing join is unpromoted when doing filtering for
        # already promoted join.
        qs = Charlie.objects.annotate(Count("alfa__name")).filter(
            alfa__name__isnull=False
        )
        self.assertIn(" INNER JOIN ", str(qs.query))
        # But, as the join is nullable first use by annotate will be LOUTER
        qs = Charlie.objects.annotate(Count("alfa__name"))
        self.assertIn(" LEFT OUTER JOIN ", str(qs.query))