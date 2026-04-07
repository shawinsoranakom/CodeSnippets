def test02_PointExceptions(self):
        "Testing Point exceptions"
        msg = "Invalid parameters given for Point initialization."
        for i in (range(1), range(4)):
            with (
                self.subTest(i=i),
                self.assertRaisesMessage(TypeError, msg),
            ):
                Point(i)