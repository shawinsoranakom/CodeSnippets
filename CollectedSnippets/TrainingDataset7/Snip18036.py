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
                "Error: Ensure this value has at most %s characters (it has %s).\n"
                "Superuser created successfully."
                % (user_field.max_length, len(invalid_username)),
            )