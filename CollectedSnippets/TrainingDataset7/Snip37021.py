def test_jsi18n_USE_I18N_False(self):
        response = self.client.get("/jsi18n/")
        # default plural function
        self.assertContains(
            response,
            "django.pluralidx = function(count) { return (count == 1) ? 0 : 1; };",
        )
        self.assertNotContains(response, "var newcatalog =")