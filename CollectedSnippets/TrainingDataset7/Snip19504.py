def test_register_no_kwargs_error(self):
        registry = CheckRegistry()
        msg = "Check functions must accept keyword arguments (**kwargs)."
        with self.assertRaisesMessage(TypeError, msg):

            @registry.register
            def no_kwargs(app_configs, databases):
                pass