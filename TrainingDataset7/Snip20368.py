def test_too_few_args(self):
        msg = "'NullIf' takes exactly 2 arguments (1 given)"
        with self.assertRaisesMessage(TypeError, msg):
            NullIf("name")