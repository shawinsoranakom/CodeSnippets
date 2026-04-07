def articles_from_same_day_1(self):
        return Article.objects.filter(pub_date=self.pub_date).exclude(id=self.id)