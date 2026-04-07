def test_invalid_function(self):
        for invalid_function in [any, self.test_invalid_function]:
            with self.subTest(invalid_function):
                with self.assertRaisesMessage(
                    InvalidTask,
                    "Task function must be defined at a module level.",
                ):
                    task()(invalid_function)