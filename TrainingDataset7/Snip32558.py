def test_international(self):
        a = InternationalArticle.objects.create(
            headline="Girl wins €12.500 in lottery",
            pub_date=datetime.datetime(2005, 7, 28),
        )
        self.assertEqual(str(a), "Girl wins €12.500 in lottery")