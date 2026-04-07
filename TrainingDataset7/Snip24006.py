def test01_init(self):
        "Testing Envelope initialization."
        e1 = Envelope((0, 0, 5, 5))
        Envelope(0, 0, 5, 5)
        Envelope(0, "0", "5", 5)  # Thanks to ww for this
        Envelope(e1._envelope)
        with self.assertRaises(GDALException):
            Envelope((5, 5, 0, 0))
        with self.assertRaises(GDALException):
            Envelope(5, 5, 0, 0)
        with self.assertRaises(GDALException):
            Envelope((0, 0, 5, 5, 3))
        with self.assertRaises(GDALException):
            Envelope(())
        with self.assertRaises(ValueError):
            Envelope(0, "a", 5, 5)
        with self.assertRaises(TypeError):
            Envelope("foo")
        with self.assertRaises(GDALException):
            Envelope((1, 1, 0, 0))
        # Shouldn't raise an exception for min_x == max_x or min_y == max_y
        Envelope(0, 0, 0, 0)