def test_tickets_7698_10202(self):
        # People like to slice with '0' as the high-water mark.
        self.assertSequenceEqual(Article.objects.all()[0:0], [])
        self.assertSequenceEqual(Article.objects.all()[0:0][:10], [])
        self.assertEqual(Article.objects.all()[:0].count(), 0)
        msg = "Cannot change a query once a slice has been taken."
        with self.assertRaisesMessage(TypeError, msg):
            Article.objects.all()[:0].latest("created")