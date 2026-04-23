def test_get_namespace_precedence(self):
        # All of these apps define an `Article` model. The one defined first in
        # INSTALLED_APPS, takes precedence.
        import model_forms.models

        namespace = shell.Command().get_namespace()
        self.assertIs(namespace.get("Article"), model_forms.models.Article)