def test_create(self):
        # You can also instantiate an Article by passing the Reporter's ID
        # instead of a Reporter object.
        a3 = Article(
            headline="Third article",
            pub_date=datetime.date(2005, 7, 27),
            reporter_id=self.r.id,
        )
        a3.save()
        self.assertEqual(a3.reporter.id, self.r.id)

        # Similarly, the reporter ID can be a string.
        a4 = Article(
            headline="Fourth article",
            pub_date=datetime.date(2005, 7, 27),
            reporter_id=str(self.r.id),
        )
        a4.save()
        self.assertEqual(repr(a4.reporter), "<Reporter: John Smith>")