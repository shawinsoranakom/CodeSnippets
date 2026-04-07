def test_percent_formatting_in_blocktranslate(self):
        """
        Python's %-formatting is properly escaped in blocktranslate, singular,
        or plural.
        """
        t_sing = self.get_template(
            "{% load i18n %}{% blocktranslate %}There are %(num_comments)s comments"
            "{% endblocktranslate %}"
        )
        t_plur = self.get_template(
            "{% load i18n %}{% blocktranslate count num as number %}"
            "%(percent)s% represents {{ num }} object{% plural %}"
            "%(percent)s% represents {{ num }} objects{% endblocktranslate %}"
        )
        with translation.override("de"):
            # Strings won't get translated as they don't match after escaping %
            self.assertEqual(
                t_sing.render(Context({"num_comments": 42})),
                "There are %(num_comments)s comments",
            )
            self.assertEqual(
                t_plur.render(Context({"percent": 42, "num": 1})),
                "%(percent)s% represents 1 object",
            )
            self.assertEqual(
                t_plur.render(Context({"percent": 42, "num": 4})),
                "%(percent)s% represents 4 objects",
            )