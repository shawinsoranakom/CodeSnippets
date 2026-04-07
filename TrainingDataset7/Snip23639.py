def test_setup_adds_args_kwargs_request(self):
        request = self.rf.get("/")
        args = ("arg 1", "arg 2")
        kwargs = {"kwarg_1": 1, "kwarg_2": "year"}

        view = View()
        view.setup(request, *args, **kwargs)
        self.assertEqual(request, view.request)
        self.assertEqual(args, view.args)
        self.assertEqual(kwargs, view.kwargs)