def test_users_url(self):
        with translation.override("en"):
            self.assertEqual(reverse("users"), "/en/users/")

        with translation.override("nl"):
            self.assertEqual(reverse("users"), "/nl/gebruikers/")
            self.assertEqual(reverse("prefixed_xml"), "/nl/prefixed.xml")

        with translation.override("pt-br"):
            self.assertEqual(reverse("users"), "/pt-br/usuarios/")