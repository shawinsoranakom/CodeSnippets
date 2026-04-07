def test_pad_negative_length(self):
        for function in (LPad, RPad):
            with self.subTest(function=function):
                with self.assertRaisesMessage(
                    ValueError, "'length' must be greater or equal to 0."
                ):
                    function("name", -1)