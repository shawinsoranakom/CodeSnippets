def test_long_unicode_textfield(self):
        # TextFields can hold more than 4000 bytes also when they are
        # less than 4000 characters
        a = Article.objects.create(
            headline="Really, really big",
            pub_date=datetime.datetime.now(),
            article_text="\u05d0\u05d1\u05d2" * 1000,
        )
        a = Article.objects.get(pk=a.pk)
        self.assertEqual(len(a.article_text), 3000)