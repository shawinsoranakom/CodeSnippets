def test_rotate_invalid_params(self):
        angle = math.pi
        bad_params_tests = [
            {"angle": angle, "origin": 0},
            {"angle": angle, "origin": [0, 0]},
        ]
        msg = "origin argument must be a Point"
        for params in bad_params_tests:
            with self.subTest(params=params), self.assertRaisesMessage(TypeError, msg):
                functions.Rotate("mpoly", **params)