def test_slicing_cannot_reorder_queryset_once_sliced(self):
        msg = "Cannot reorder a query once a slice has been taken."
        with self.assertRaisesMessage(TypeError, msg):
            Article.objects.all()[0:5].order_by("id")