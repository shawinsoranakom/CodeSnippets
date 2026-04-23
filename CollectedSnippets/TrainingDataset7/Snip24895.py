def test_account_register(self):
        with translation.override("en"):
            self.assertEqual(reverse("account:register"), "/en/account/register/")
            self.assertEqual(
                reverse("account:register-as-path"), "/en/account/register-as-path/"
            )

        with translation.override("nl"):
            self.assertEqual(reverse("account:register"), "/nl/profiel/registreren/")
            self.assertEqual(
                reverse("account:register-as-path"), "/nl/profiel/registreren-als-pad/"
            )