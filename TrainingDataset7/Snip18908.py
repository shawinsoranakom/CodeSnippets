def test_manually_specify_primary_key(self):
        # You can manually specify the primary key when creating a new object.
        a101 = Article(
            id=101,
            headline="Article 101",
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        a101.save()
        a101 = Article.objects.get(pk=101)
        self.assertEqual(a101.headline, "Article 101")