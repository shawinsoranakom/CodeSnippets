def test_calling_command_with_app_labels_and_parameters_should_be_ok(self):
        out = StringIO()
        management.call_command("hal", "myapp", "--verbosity", "3", stdout=out)
        self.assertIn(
            "Dave, my mind is going. I can feel it. I can feel it.\n", out.getvalue()
        )