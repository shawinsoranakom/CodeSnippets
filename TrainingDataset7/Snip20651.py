def test_annotate_textfield(self):
        Article.objects.create(
            title="How to Django",
            text="This is about How to Django.",
            written=timezone.now(),
        )
        Article.objects.create(
            title="How to Tango",
            text="Won't find anything here.",
            written=timezone.now(),
        )
        articles = Article.objects.annotate(title_pos=StrIndex("text", "title"))
        self.assertQuerySetEqual(
            articles.order_by("title"), [15, 0], lambda a: a.title_pos
        )