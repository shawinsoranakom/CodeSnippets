def test_fields_with_fk_via_option_interactive(self):
        new_io = StringIO()
        group = Group.objects.create(name="mygroup")
        email = Email.objects.create(email="mymail@gmail.com")

        @mock_inputs({"password": "nopasswd"})
        def test(self):
            call_command(
                "createsuperuser",
                interactive=True,
                username=email.pk,
                email=email.email,
                group=group.pk,
                stdout=new_io,
                stdin=MockTTY(),
            )

            command_output = new_io.getvalue().strip()
            self.assertEqual(command_output, "Superuser created successfully.")
            u = CustomUserWithFK._default_manager.get(email=email)
            self.assertEqual(u.username, email)
            self.assertEqual(u.group, group)

        test(self)