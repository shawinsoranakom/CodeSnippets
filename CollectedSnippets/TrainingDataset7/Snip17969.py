def test_fields_with_m2m(self):
        new_io = StringIO()
        org_id_1 = Organization.objects.create(name="Organization 1").pk
        org_id_2 = Organization.objects.create(name="Organization 2").pk
        call_command(
            "createsuperuser",
            interactive=False,
            username="joe",
            orgs=[org_id_1, org_id_2],
            stdout=new_io,
        )
        command_output = new_io.getvalue().strip()
        self.assertEqual(command_output, "Superuser created successfully.")
        user = CustomUserWithM2M._default_manager.get(username="joe")
        self.assertEqual(user.orgs.count(), 2)