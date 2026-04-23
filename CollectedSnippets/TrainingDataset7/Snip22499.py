def test_choicefield_callable_mapping(self):
        def choices():
            return {"J": "John", "P": "Paul"}

        f = ChoiceField(choices=choices)
        self.assertEqual("J", f.clean("J"))