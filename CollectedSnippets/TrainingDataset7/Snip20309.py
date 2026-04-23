def __str__(self):
        return "Comment to %s (%s)" % (self.article.title, self.pub_date)