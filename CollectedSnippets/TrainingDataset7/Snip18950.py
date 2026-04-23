def test_refresh_unsaved(self):
        pub_date = datetime.now()
        a = Article.objects.create(pub_date=pub_date)
        a2 = Article(id=a.pk)
        with self.assertNumQueries(1):
            a2.refresh_from_db()
        self.assertEqual(a2.pub_date, pub_date)
        self.assertEqual(a2._state.db, "default")