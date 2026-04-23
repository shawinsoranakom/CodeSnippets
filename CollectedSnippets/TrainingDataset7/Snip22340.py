def test_parsing_errors(self):
        "There are various ways that the flatpages template tag won't parse"

        def render(t):
            return Template(t).render(Context())

        msg = (
            "get_flatpages expects a syntax of get_flatpages "
            "['url_starts_with'] [for user] as context_name"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            render("{% load flatpages %}{% get_flatpages %}")
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            render("{% load flatpages %}{% get_flatpages as %}")
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            render("{% load flatpages %}{% get_flatpages cheesecake flatpages %}")
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            render("{% load flatpages %}{% get_flatpages as flatpages asdf %}")
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            render(
                "{% load flatpages %}{% get_flatpages cheesecake user as flatpages %}"
            )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            render("{% load flatpages %}{% get_flatpages for user as flatpages asdf %}")
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            render(
                "{% load flatpages %}"
                "{% get_flatpages prefix for user as flatpages asdf %}"
            )