def test_unicode_values(self):
        Author.objects.create(name="ツリー")
        Author.objects.create(name="皇帝")
        Author.objects.create(name="皇帝 ツリー")
        authors = Author.objects.annotate(sb=StrIndex("name", Value("リ")))
        self.assertQuerySetEqual(authors.order_by("name"), [2, 0, 5], lambda a: a.sb)