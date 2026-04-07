def test_regr_count_default(self):
        msg = "RegrCount does not allow default."
        with self.assertRaisesMessage(TypeError, msg):
            RegrCount(y="int2", x="int1", default=0)