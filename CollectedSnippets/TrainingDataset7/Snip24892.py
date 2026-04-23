def test_translate_url_utility(self):
        with translation.override("en"):
            self.assertEqual(
                translate_url("/en/nonexistent/", "nl"), "/en/nonexistent/"
            )
            self.assertEqual(translate_url("/en/users/", "nl"), "/nl/gebruikers/")
            # Namespaced URL
            self.assertEqual(
                translate_url("/en/account/register/", "nl"), "/nl/profiel/registreren/"
            )
            # path() URL pattern
            self.assertEqual(
                translate_url("/en/account/register-as-path/", "nl"),
                "/nl/profiel/registreren-als-pad/",
            )
            self.assertEqual(translation.get_language(), "en")
            # re_path() URL with parameters.
            self.assertEqual(
                translate_url("/en/with-arguments/regular-argument/", "nl"),
                "/nl/with-arguments/regular-argument/",
            )
            self.assertEqual(
                translate_url(
                    "/en/with-arguments/regular-argument/optional.html", "nl"
                ),
                "/nl/with-arguments/regular-argument/optional.html",
            )
            # path() URL with parameter.
            self.assertEqual(
                translate_url("/en/path-with-arguments/regular-argument/", "nl"),
                "/nl/path-with-arguments/regular-argument/",
            )

        with translation.override("nl"):
            self.assertEqual(translate_url("/nl/gebruikers/", "en"), "/en/users/")
            self.assertEqual(translation.get_language(), "nl")