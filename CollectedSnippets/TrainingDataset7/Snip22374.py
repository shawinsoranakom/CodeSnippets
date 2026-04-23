def __str__(self):
        try:
            return self.active_translation.title
        except ArticleTranslation.DoesNotExist:
            return "[No translation found]"