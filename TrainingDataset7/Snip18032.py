def test(self):
            call_command(
                "createsuperuser",
                interactive=True,
                first_name=first_name,
                date_of_birth="1970-01-01",
                email="joey@example.com",
                stdin=MockTTY(),
                stdout=new_io,
                stderr=new_io,
            )
            self.assertEqual(
                new_io.getvalue().strip(),
                "The password is too similar to the first name.\n"
                "Superuser created successfully.",
            )