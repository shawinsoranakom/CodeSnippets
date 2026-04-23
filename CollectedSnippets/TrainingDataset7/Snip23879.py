def test_latest_sliced_queryset(self):
        msg = "Cannot change a query once a slice has been taken."
        with self.assertRaisesMessage(TypeError, msg):
            Article.objects.all()[0:5].latest()