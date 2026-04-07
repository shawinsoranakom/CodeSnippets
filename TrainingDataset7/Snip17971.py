def test_fields_with_m2m_interactive_blank(self):
        new_io = StringIO()
        org_id = Organization.objects.create(name="Organization").pk
        entered_orgs = [str(org_id), " "]

        def return_orgs():
            return entered_orgs.pop()

        @mock_inputs(
            {
                "password": "nopasswd",
                "Username: ": "joe",
                "Orgs (Organization.id): ": return_orgs,
            }
        )
        def test(self):
            call_command(
                "createsuperuser",
                interactive=True,
                stdout=new_io,
                stderr=new_io,
                stdin=MockTTY(),
            )
            self.assertEqual(
                new_io.getvalue().strip(),
                "Error: This field cannot be blank.\n"
                "Superuser created successfully.",
            )

        test(self)