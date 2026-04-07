def test_refresh_fk_on_delete_set_null(self):
        a = Article.objects.create(
            headline="Parrot programs in Python",
            pub_date=datetime(2005, 7, 28),
        )
        s1 = SelfRef.objects.create(article=a)
        a.delete()
        s1.refresh_from_db()
        self.assertIsNone(s1.article_id)
        self.assertIsNone(s1.article)