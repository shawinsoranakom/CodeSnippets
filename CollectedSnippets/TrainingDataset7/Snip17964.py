def test_fields_with_fk_interactive(self):
        new_io = StringIO()
        group = Group.objects.create(name="mygroup")
        email = Email.objects.create(email="mymail@gmail.com")

        @mock_inputs(
            {
                "password": "nopasswd",
                "Username (Email.id): ": email.pk,
                "Email (Email.email): ": email.email,
                "Group (Group.id): ": group.pk,
            }
        )
        def test(self):
            call_command(
                "createsuperuser",
                interactive=True,
                stdout=new_io,
                stdin=MockTTY(),
            )

            command_output = new_io.getvalue().strip()
            self.assertEqual(command_output, "Superuser created successfully.")
            u = CustomUserWithFK._default_manager.get(email=email)
            self.assertEqual(u.username, email)
            self.assertEqual(u.group, group)

        test(self)