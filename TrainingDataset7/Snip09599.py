def _comment_sql(self, comment):
        comment_sql = super()._comment_sql(comment)
        return f" COMMENT {comment_sql}"