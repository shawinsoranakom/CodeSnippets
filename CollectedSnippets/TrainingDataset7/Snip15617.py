def test_prevent_double_registration_for_custom_admin(self):
        class PersonAdmin(admin.ModelAdmin):
            pass

        self.site.register(Person, PersonAdmin)
        msg = (
            "The model Person is already registered with "
            "'admin_registration.PersonAdmin'."
        )
        with self.assertRaisesMessage(AlreadyRegistered, msg):
            self.site.register(Person, PersonAdmin)