def test_usermodel_without_password(self):
        new_io = StringIO()
        call_command(
            "createsuperuser",
            interactive=False,
            stdin=MockTTY(),
            stdout=new_io,
            stderr=new_io,
            username="username",
        )
        self.assertEqual(new_io.getvalue().strip(), "Superuser created successfully.")