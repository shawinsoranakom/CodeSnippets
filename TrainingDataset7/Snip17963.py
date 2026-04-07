def test_fields_with_fk(self):
        new_io = StringIO()
        group = Group.objects.create(name="mygroup")
        email = Email.objects.create(email="mymail@gmail.com")
        call_command(
            "createsuperuser",
            interactive=False,
            username=email.pk,
            email=email.email,
            group=group.pk,
            stdout=new_io,
        )
        command_output = new_io.getvalue().strip()
        self.assertEqual(command_output, "Superuser created successfully.")
        u = CustomUserWithFK._default_manager.get(email=email)
        self.assertEqual(u.username, email)
        self.assertEqual(u.group, group)

        non_existent_email = "mymail2@gmail.com"
        msg = "email instance with email %r is not a valid choice." % non_existent_email
        with self.assertRaisesMessage(CommandError, msg):
            call_command(
                "createsuperuser",
                interactive=False,
                username=email.pk,
                email=non_existent_email,
                stdout=new_io,
            )