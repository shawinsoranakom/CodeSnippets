def test_sliced_queryset(self):
        msg = "Cannot use 'limit' or 'offset' with delete()."
        with self.assertRaisesMessage(TypeError, msg):
            M.objects.all()[0:5].delete()