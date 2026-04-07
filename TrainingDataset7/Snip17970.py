def test_fields_with_m2m_interactive(self):
        new_io = StringIO()
        org_id_1 = Organization.objects.create(name="Organization 1").pk
        org_id_2 = Organization.objects.create(name="Organization 2").pk

        @mock_inputs(
            {
                "password": "nopasswd",
                "Username: ": "joe",
                "Orgs (Organization.id): ": "%s, %s" % (org_id_1, org_id_2),
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
            user = CustomUserWithM2M._default_manager.get(username="joe")
            self.assertEqual(user.orgs.count(), 2)

        test(self)