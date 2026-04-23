def test_no_reordering_after_slicing(self):
        msg = "Cannot reverse a query once a slice has been taken."
        qs = Article.objects.all()[0:2]
        with self.assertRaisesMessage(TypeError, msg):
            qs.reverse()
        with self.assertRaisesMessage(TypeError, msg):
            qs.last()