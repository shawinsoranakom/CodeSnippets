def test(self):
            call_command(
                "createsuperuser",
                interactive=True,
                stdout=new_io,
                stdin=MockTTY(),
            )
            command_output = new_io.getvalue().strip()
            self.assertEqual(command_output, "Superuser created successfully.")
            user = CustomUserWithM2M._default_manager.get(username="joe")
            self.assertEqual(user.orgs.count(), 2)