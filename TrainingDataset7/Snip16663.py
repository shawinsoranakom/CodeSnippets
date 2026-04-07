def assert_contains_year_link(self, response, date):
        self.assertContains(response, '?release_date__year=%d"' % date.year)