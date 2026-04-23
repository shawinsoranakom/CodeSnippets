def test_in_bulk_sliced_queryset(self):
        msg = "Cannot use 'limit' or 'offset' with in_bulk()."
        with self.assertRaisesMessage(TypeError, msg):
            Article.objects.all()[0:5].in_bulk([self.a1.id, self.a2.id])