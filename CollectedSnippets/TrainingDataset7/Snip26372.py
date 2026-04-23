def test_joined_extra(self):
        new_article1 = self.r.article_set.create(
            headline="John's second story",
            pub_date=datetime.date(2005, 7, 29),
        )
        self.r2.article_set.create(
            headline="Paul's story",
            pub_date=datetime.date(2006, 1, 17),
        )
        # The automatically joined table has a predictable name.
        self.assertSequenceEqual(
            Article.objects.filter(reporter__first_name__exact="John").extra(
                where=["many_to_one_reporter.last_name='Smith'"]
            ),
            [new_article1, self.a],
        )
        # ... and should work fine with the string that comes out of
        # forms.Form.cleaned_data.
        self.assertQuerySetEqual(
            (
                Article.objects.filter(reporter__first_name__exact="John").extra(
                    where=["many_to_one_reporter.last_name=%s"],
                    params=["Smith"],
                )
            ),
            [new_article1, self.a],
        )