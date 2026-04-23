def test_slicing_cannot_filter_queryset_once_sliced(self):
        msg = "Cannot filter a query once a slice has been taken."
        with self.assertRaisesMessage(TypeError, msg):
            Article.objects.all()[0:5].filter(id=1)