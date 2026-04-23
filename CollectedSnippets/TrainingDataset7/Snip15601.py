def test_default_ordering(self):
        """
        The default ordering should be by name, as specified in the inner Meta
        class.
        """
        inline = SongInlineDefaultOrdering(self.band, site)
        names = [s.name for s in inline.get_queryset(request)]
        self.assertEqual(["Dude (Looks Like a Lady)", "Jaded", "Pink"], names)