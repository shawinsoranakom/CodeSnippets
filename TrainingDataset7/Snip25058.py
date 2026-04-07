def test_plural(self):
        """
        Test plurals with ngettext. French differs from English in that 0 is
        singular.
        """
        self.assertEqual(
            ngettext("%(num)d year", "%(num)d years", 0) % {"num": 0},
            "0 année",
        )
        self.assertEqual(
            ngettext("%(num)d year", "%(num)d years", 2) % {"num": 2},
            "2 ans",
        )
        self.assertEqual(
            ngettext("%(size)d byte", "%(size)d bytes", 0) % {"size": 0}, "0 octet"
        )
        self.assertEqual(
            ngettext("%(size)d byte", "%(size)d bytes", 2) % {"size": 2}, "2 octets"
        )