def test(self):
            call_command(
                "createsuperuser",
                interactive=True,
                stdout=new_io,
                stderr=new_io,
                stdin=MockTTY(),
            )
            self.assertEqual(
                new_io.getvalue().strip(),
                "Error: This field cannot be blank.\n"
                "Superuser created successfully.",
            )