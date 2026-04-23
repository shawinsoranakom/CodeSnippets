def test_args_kwargs_request_on_self(self):
        """
        Test a view only has args, kwargs & request once `as_view`
        has been called.
        """
        bare_view = InstanceView()
        view = InstanceView.as_view()(self.rf.get("/"))
        for attribute in ("args", "kwargs", "request"):
            self.assertNotIn(attribute, dir(bare_view))
            self.assertIn(attribute, dir(view))