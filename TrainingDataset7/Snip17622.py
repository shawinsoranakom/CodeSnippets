def test_user_verbose_names_translatable(self):
        "Default User model verbose names are translatable (#19945)"
        with translation.override("en"):
            self.assertEqual(User._meta.verbose_name, "user")
            self.assertEqual(User._meta.verbose_name_plural, "users")
        with translation.override("es"):
            self.assertEqual(User._meta.verbose_name, "usuario")
            self.assertEqual(User._meta.verbose_name_plural, "usuarios")