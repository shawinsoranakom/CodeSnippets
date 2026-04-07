def test_register_run_checks_non_iterable(self):
        registry = CheckRegistry()

        @registry.register
        def return_non_iterable(**kwargs):
            return Error("Message")

        msg = (
            "The function %r did not return a list. All functions registered "
            "with the checks registry must return a list." % return_non_iterable
        )
        with self.assertRaisesMessage(TypeError, msg):
            registry.run_checks()