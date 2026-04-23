def test_callable(self):
        def get_choices():
            return {
                "C": _("Club"),
                "D": _("Diamond"),
                "H": _("Heart"),
                "S": _("Spade"),
            }

        get_choices_spy = mock.Mock(wraps=get_choices)
        output = normalize_choices(get_choices_spy)

        get_choices_spy.assert_not_called()
        self.assertIsInstance(output, CallableChoiceIterator)
        self.assertEqual(output, self.expected)
        get_choices_spy.assert_called_once()