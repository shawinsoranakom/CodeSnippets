def test_long_textfield(self):
        # TextFields can hold more than 4000 characters (this was broken in
        # Oracle).
        a = Article.objects.create(
            headline="Really, really big",
            pub_date=datetime.datetime.now(),
            article_text="ABCDE" * 1000,
        )
        a = Article.objects.get(pk=a.pk)
        self.assertEqual(len(a.article_text), 5000)