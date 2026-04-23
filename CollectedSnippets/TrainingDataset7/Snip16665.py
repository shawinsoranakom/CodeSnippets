def assert_contains_day_link(self, response, date):
        self.assertContains(
            response,
            "?release_date__day=%d&amp;"
            'release_date__month=%d&amp;release_date__year=%d"'
            % (date.day, date.month, date.year),
        )