def assertNumContains(self, haystack, needle, count):
        real_count = haystack.count(needle)
        self.assertEqual(
            real_count,
            count,
            "Found %d instances of '%s', expected %d" % (real_count, needle, count),
        )