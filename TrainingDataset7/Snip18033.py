def test(self):
            call_command(
                "createsuperuser",
                interactive=True,
                stdin=MockTTY(),
                stdout=new_io,
                stderr=new_io,
            )
            self.assertEqual(
                new_io.getvalue().strip(),
                "This password is entirely numeric.\n"
                "Superuser created successfully.",
            )