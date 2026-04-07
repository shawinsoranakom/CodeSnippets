def test_multivalue_deep_copy(self):
        """
        #19298 -- MultiValueField needs to override the default as it needs
        to deep-copy subfields:
        """

        class ChoicesField(MultiValueField):
            def __init__(self, fields=(), *args, **kwargs):
                fields = (
                    ChoiceField(label="Rank", choices=((1, 1), (2, 2))),
                    CharField(label="Name", max_length=10),
                )
                super().__init__(fields=fields, *args, **kwargs)

        field = ChoicesField()
        field2 = copy.deepcopy(field)
        self.assertIsInstance(field2, ChoicesField)
        self.assertIsNot(field2.fields, field.fields)
        self.assertIsNot(field2.fields[0].choices, field.fields[0].choices)