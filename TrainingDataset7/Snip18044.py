def test(self):
            call_command(
                "createsuperuser",
                username="janet",
                interactive=True,
                stdin=MockTTY(),
                stdout=new_io,
                stderr=new_io,
            )
            msg = (
                "Error: That username is already taken.\n"
                "Superuser created successfully."
            )
            self.assertEqual(new_io.getvalue().strip(), msg)