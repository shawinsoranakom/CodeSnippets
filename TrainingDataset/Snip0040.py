 def mapper(self, _, line):

        url = self.extract_url(line)
        period = self.extract_year_month(line)
        yield (period, url), 1
