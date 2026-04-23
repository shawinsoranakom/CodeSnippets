def test_non_ascii_verbose_name(self):
        @mock_inputs(
            {
                "password": "nopasswd",
                "Uživatel (leave blank to use '%s'): "
                % get_default_username(): "foo",  # username (cz)
                "email": "nolocale@somewhere.org",
            }
        )
        def test(self):
            username_field = User._meta.get_field("username")
            old_verbose_name = username_field.verbose_name
            username_field.verbose_name = _("u\u017eivatel")
            new_io = StringIO()
            try:
                call_command(
                    "createsuperuser",
                    interactive=True,
                    stdout=new_io,
                    stdin=MockTTY(),
                )
            finally:
                username_field.verbose_name = old_verbose_name

            command_output = new_io.getvalue().strip()
            self.assertEqual(command_output, "Superuser created successfully.")

        test(self)