def test_unique_for_date_with_nullable_date(self):
        """
        unique_for_date/year/month checks shouldn't trigger when the
        associated DateField is None.
        """
        FlexibleDatePost.objects.create(
            title="Django 1.0 is released",
            slug="Django 1.0",
            subtitle="Finally",
            posted=datetime.date(2008, 9, 3),
        )
        p = FlexibleDatePost(title="Django 1.0 is released")
        p.full_clean()

        p = FlexibleDatePost(slug="Django 1.0")
        p.full_clean()

        p = FlexibleDatePost(subtitle="Finally")
        p.full_clean()