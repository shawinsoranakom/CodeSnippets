def createsuperuser():
            new_io = StringIO()
            call_command(
                "createsuperuser",
                interactive=True,
                email="joe@somewhere.org",
                stdout=new_io,
                stdin=MockTTY(),
            )
            command_output = new_io.getvalue().strip()
            self.assertEqual(command_output, "Superuser created successfully.")