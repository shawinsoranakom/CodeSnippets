def test_restrictions_with_no_joining_columns(self):
        """
        It's possible to create a working related field that doesn't
        use any joining columns, as long as an extra restriction is supplied.
        """
        a = SlugPage.objects.get(slug="a")
        self.assertEqual(
            [p.slug for p in SlugPage.objects.filter(ascendants=a)],
            ["a", "a/a", "a/b", "a/b/a"],
        )
        self.assertEqual(
            [p.slug for p in a.descendants.all()],
            ["a", "a/a", "a/b", "a/b/a"],
        )

        aba = SlugPage.objects.get(slug="a/b/a")
        self.assertEqual(
            [p.slug for p in SlugPage.objects.filter(descendants__in=[aba])],
            ["a", "a/b", "a/b/a"],
        )
        self.assertEqual(
            [p.slug for p in aba.ascendants.all()],
            ["a", "a/b", "a/b/a"],
        )