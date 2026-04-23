def test_ngettext_lazy_format_style(self):
        simple_with_format = ngettext_lazy("{} good result", "{} good results")
        simple_context_with_format = npgettext_lazy(
            "Exclamation", "{} good result", "{} good results"
        )

        with translation.override("de"):
            self.assertEqual(simple_with_format.format(1), "1 gutes Resultat")
            self.assertEqual(simple_with_format.format(4), "4 guten Resultate")
            self.assertEqual(simple_context_with_format.format(1), "1 gutes Resultat!")
            self.assertEqual(simple_context_with_format.format(4), "4 guten Resultate!")

        complex_nonlazy = ngettext_lazy(
            "Hi {name}, {num} good result", "Hi {name}, {num} good results", 4
        )
        complex_deferred = ngettext_lazy(
            "Hi {name}, {num} good result", "Hi {name}, {num} good results", "num"
        )
        complex_context_nonlazy = npgettext_lazy(
            "Greeting",
            "Hi {name}, {num} good result",
            "Hi {name}, {num} good results",
            4,
        )
        complex_context_deferred = npgettext_lazy(
            "Greeting",
            "Hi {name}, {num} good result",
            "Hi {name}, {num} good results",
            "num",
        )
        with translation.override("de"):
            self.assertEqual(
                complex_nonlazy.format(num=4, name="Jim"),
                "Hallo Jim, 4 guten Resultate",
            )
            self.assertEqual(
                complex_deferred.format(name="Jim", num=1),
                "Hallo Jim, 1 gutes Resultat",
            )
            self.assertEqual(
                complex_deferred.format(name="Jim", num=5),
                "Hallo Jim, 5 guten Resultate",
            )
            with self.assertRaisesMessage(KeyError, "Your dictionary lacks key"):
                complex_deferred.format(name="Jim")
            self.assertEqual(
                complex_context_nonlazy.format(num=4, name="Jim"),
                "Willkommen Jim, 4 guten Resultate",
            )
            self.assertEqual(
                complex_context_deferred.format(name="Jim", num=1),
                "Willkommen Jim, 1 gutes Resultat",
            )
            self.assertEqual(
                complex_context_deferred.format(name="Jim", num=5),
                "Willkommen Jim, 5 guten Resultate",
            )
            with self.assertRaisesMessage(KeyError, "Your dictionary lacks key"):
                complex_context_deferred.format(name="Jim")