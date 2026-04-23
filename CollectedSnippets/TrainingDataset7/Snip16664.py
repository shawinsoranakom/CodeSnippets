def assert_contains_month_link(self, response, date):
        self.assertContains(
            response,
            '?release_date__month=%d&amp;release_date__year=%d"'
            % (date.month, date.year),
        )