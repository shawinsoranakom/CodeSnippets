def test_usermodel_without_password_interactive(self):
        new_io = StringIO()

        @mock_inputs({"username": "username"})
        def test(self):
            call_command(
                "createsuperuser",
                interactive=True,
                stdin=MockTTY(),
                stdout=new_io,
                stderr=new_io,
            )
            self.assertEqual(
                new_io.getvalue().strip(), "Superuser created successfully."
            )

        test(self)