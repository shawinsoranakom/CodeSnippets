def get_ordered_articles(self):
        return Article.objects.order_by("name")