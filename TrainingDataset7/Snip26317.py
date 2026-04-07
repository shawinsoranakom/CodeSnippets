def test_reverse_add(self):
        # Adding via the 'other' end of an m2m
        a5 = Article(headline="NASA finds intelligent life on Mars")
        a5.save()
        self.p2.article_set.add(a5)
        self.assertSequenceEqual(
            self.p2.article_set.all(),
            [self.a3, a5, self.a2, self.a4],
        )
        self.assertSequenceEqual(a5.publications.all(), [self.p2])

        # Adding via the other end using keywords
        a6 = self.p2.article_set.create(headline="Carbon-free diet works wonders")
        self.assertSequenceEqual(
            self.p2.article_set.all(),
            [a6, self.a3, a5, self.a2, self.a4],
        )
        a6 = self.p2.article_set.all()[3]
        self.assertSequenceEqual(
            a6.publications.all(),
            [self.p4, self.p2, self.p3, self.p1],
        )