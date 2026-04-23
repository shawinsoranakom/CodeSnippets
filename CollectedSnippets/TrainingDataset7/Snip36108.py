def test_iterator_non_canonical(self):
        # Canonical form is list of 2-tuple, but nested lists should work.
        def generator():
            yield ["C", _("Club")]
            yield ["D", _("Diamond")]
            yield ["H", _("Heart")]
            yield ["S", _("Spade")]

        choices = generator()
        self.assertEqual(normalize_choices(choices), self.expected)