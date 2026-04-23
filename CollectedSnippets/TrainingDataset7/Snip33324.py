def test_percent_in_translatable_block(self):
        t_sing = self.get_template(
            "{% load i18n %}{% blocktranslate %}The result was {{ percent }}%"
            "{% endblocktranslate %}"
        )
        t_plur = self.get_template(
            "{% load i18n %}{% blocktranslate count num as number %}"
            "{{ percent }}% represents {{ num }} object{% plural %}"
            "{{ percent }}% represents {{ num }} objects{% endblocktranslate %}"
        )
        with translation.override("de"):
            self.assertEqual(
                t_sing.render(Context({"percent": 42})), "Das Ergebnis war 42%"
            )
            self.assertEqual(
                t_plur.render(Context({"percent": 42, "num": 1})),
                "42% stellt 1 Objekt dar",
            )
            self.assertEqual(
                t_plur.render(Context({"percent": 42, "num": 4})),
                "42% stellt 4 Objekte dar",
            )