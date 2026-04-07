def test_wrapped_class_not_a_model_admin(self):
        with self.assertRaisesMessage(
            ValueError, "Wrapped class must subclass ModelAdmin."
        ):
            register(Person)(CustomSite)