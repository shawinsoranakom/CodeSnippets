def test_regex_non_string(self):
        """
        A regex lookup does not fail on non-string fields
        """
        s = Season.objects.create(year=2013, gt=444)
        self.assertQuerySetEqual(Season.objects.filter(gt__regex=r"^444$"), [s])