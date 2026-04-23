def test_intcomma_without_number_grouping(self):
        # Regression for #17414
        with translation.override("ja"):
            self.humanize_tester([100], ["100"], "intcomma")