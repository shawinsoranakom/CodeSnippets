def test_empty_models_list_registration_fails(self):
        with self.assertRaisesMessage(
            ValueError, "At least one model must be passed to register."
        ):
            register()(NameAdmin)