def test_model_init_too_many_args(self):
        msg = "Number of args exceeds number of fields"
        with self.assertRaisesMessage(IndexError, msg):
            Worker(1, 2, 3, 4)