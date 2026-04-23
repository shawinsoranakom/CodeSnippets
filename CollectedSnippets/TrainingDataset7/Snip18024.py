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
            self.assertTrue(User.objects.filter(username=default_username).exists())