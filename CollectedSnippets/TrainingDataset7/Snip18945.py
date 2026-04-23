def test_refresh(self):
        a = Article.objects.create(pub_date=datetime.now())
        Article.objects.create(pub_date=datetime.now())
        Article.objects.filter(pk=a.pk).update(headline="new headline")
        with self.assertNumQueries(1):
            a.refresh_from_db()
            self.assertEqual(a.headline, "new headline")

        orig_pub_date = a.pub_date
        new_pub_date = a.pub_date + timedelta(10)
        Article.objects.update(headline="new headline 2", pub_date=new_pub_date)
        with self.assertNumQueries(1):
            a.refresh_from_db(fields=["headline"])
            self.assertEqual(a.headline, "new headline 2")
            self.assertEqual(a.pub_date, orig_pub_date)
        with self.assertNumQueries(1):
            a.refresh_from_db()
            self.assertEqual(a.pub_date, new_pub_date)