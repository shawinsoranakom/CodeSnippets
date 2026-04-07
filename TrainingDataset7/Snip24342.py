def test_is_counterclockwise(self):
        lr = LinearRing((0, 0), (1, 0), (0, 1), (0, 0))
        self.assertIs(lr.is_counterclockwise, True)
        lr.reverse()
        self.assertIs(lr.is_counterclockwise, False)
        msg = "Orientation of an empty LinearRing cannot be determined."
        with self.assertRaisesMessage(ValueError, msg):
            LinearRing().is_counterclockwise