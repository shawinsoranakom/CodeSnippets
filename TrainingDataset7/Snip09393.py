def _comment_sql(self, comment):
        return self.quote_value(comment or "")