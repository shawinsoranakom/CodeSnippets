def test_axis_order_invalid(self):
        msg = "SpatialReference.axis_order must be an AxisOrder instance."
        with self.assertRaisesMessage(ValueError, msg):
            SpatialReference(4326, axis_order="other")