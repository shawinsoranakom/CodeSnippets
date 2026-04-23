def test_lazy_objects(self):
        """
        Format string interpolation should work with *_lazy objects.
        """
        s = gettext_lazy("Add %(name)s")
        d = {"name": "Ringo"}
        self.assertEqual("Add Ringo", s % d)
        with translation.override("de", deactivate=True):
            self.assertEqual("Ringo hinzuf\xfcgen", s % d)
            with translation.override("pl"):
                self.assertEqual("Dodaj Ringo", s % d)

        # It should be possible to compare *_lazy objects.
        s1 = gettext_lazy("Add %(name)s")
        self.assertEqual(s, s1)
        s2 = gettext_lazy("Add %(name)s")
        s3 = gettext_lazy("Add %(name)s")
        self.assertEqual(s2, s3)
        self.assertEqual(s, s2)
        s4 = gettext_lazy("Some other string")
        self.assertNotEqual(s, s4)