def test_fields_with_m2m_and_through(self):
        msg = (
            "Required field 'orgs' specifies a many-to-many relation through "
            "model, which is not supported."
        )
        with self.assertRaisesMessage(CommandError, msg):
            call_command("createsuperuser")