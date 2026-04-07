def test_calling_command_with_parameters_and_app_labels_at_the_end_should_be_ok(
        self,
    ):
        out = StringIO()
        management.call_command("hal", "--verbosity", "3", "myapp", stdout=out)
        self.assertIn(
            "Dave, my mind is going. I can feel it. I can feel it.\n", out.getvalue()
        )