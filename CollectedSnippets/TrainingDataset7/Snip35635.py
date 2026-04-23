def test_update_slice_fail(self):
        """
        We do not support update on already sliced query sets.
        """
        method = DataPoint.objects.all()[:2].update
        msg = "Cannot update a query once a slice has been taken."
        with self.assertRaisesMessage(TypeError, msg):
            method(another_value="another thing")