def test_slicing_cannot_combine_queries_once_sliced(self):
        msg = "Cannot combine queries once a slice has been taken."
        with self.assertRaisesMessage(TypeError, msg):
            Article.objects.all()[0:1] & Article.objects.all()[4:5]