def test_ticket_18785(self):
        # Test join trimming from ticket18785
        qs = (
            Item.objects.exclude(note__isnull=False)
            .filter(name="something", creator__extra__isnull=True)
            .order_by()
        )
        self.assertEqual(1, str(qs.query).count("INNER JOIN"))
        self.assertEqual(0, str(qs.query).count("OUTER JOIN"))