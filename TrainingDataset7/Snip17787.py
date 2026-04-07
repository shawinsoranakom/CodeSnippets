def test_help_text_translation(self):
        french_help_texts = [
            "Votre mot de passe ne peut pas trop ressembler à vos autres informations "
            "personnelles.",
            "Votre mot de passe doit contenir au minimum 12 caractères.",
        ]
        form = SetPasswordForm(self.u1)
        with translation.override("fr"):
            html = form.as_p()
            for french_text in french_help_texts:
                self.assertIn(french_text, html)