def test_ngettext_lazy(self):
        simple_with_format = ngettext_lazy("%d good result", "%d good results")
        simple_context_with_format = npgettext_lazy(
            "Exclamation", "%d good result", "%d good results"
        )
        simple_without_format = ngettext_lazy("good result", "good results")
        with translation.override("de"):
            self.assertEqual(simple_with_format % 1, "1 gutes Resultat")
            self.assertEqual(simple_with_format % 4, "4 guten Resultate")
            self.assertEqual(simple_context_with_format % 1, "1 gutes Resultat!")
            self.assertEqual(simple_context_with_format % 4, "4 guten Resultate!")
            self.assertEqual(simple_without_format % 1, "gutes Resultat")
            self.assertEqual(simple_without_format % 4, "guten Resultate")

        complex_nonlazy = ngettext_lazy(
            "Hi %(name)s, %(num)d good result", "Hi %(name)s, %(num)d good results", 4
        )
        complex_deferred = ngettext_lazy(
            "Hi %(name)s, %(num)d good result",
            "Hi %(name)s, %(num)d good results",
            "num",
        )
        complex_context_nonlazy = npgettext_lazy(
            "Greeting",
            "Hi %(name)s, %(num)d good result",
            "Hi %(name)s, %(num)d good results",
            4,
        )
        complex_context_deferred = npgettext_lazy(
            "Greeting",
            "Hi %(name)s, %(num)d good result",
            "Hi %(name)s, %(num)d good results",
            "num",
        )
        with translation.override("de"):
            self.assertEqual(
                complex_nonlazy % {"num": 4, "name": "Jim"},
                "Hallo Jim, 4 guten Resultate",
            )
            self.assertEqual(
                complex_deferred % {"name": "Jim", "num": 1},
                "Hallo Jim, 1 gutes Resultat",
            )
            self.assertEqual(
                complex_deferred % {"name": "Jim", "num": 5},
                "Hallo Jim, 5 guten Resultate",
            )
            with self.assertRaisesMessage(KeyError, "Your dictionary lacks key"):
                complex_deferred % {"name": "Jim"}
            self.assertEqual(
                complex_context_nonlazy % {"num": 4, "name": "Jim"},
                "Willkommen Jim, 4 guten Resultate",
            )
            self.assertEqual(
                complex_context_deferred % {"name": "Jim", "num": 1},
                "Willkommen Jim, 1 gutes Resultat",
            )
            self.assertEqual(
                complex_context_deferred % {"name": "Jim", "num": 5},
                "Willkommen Jim, 5 guten Resultate",
            )
            with self.assertRaisesMessage(KeyError, "Your dictionary lacks key"):
                complex_context_deferred % {"name": "Jim"}