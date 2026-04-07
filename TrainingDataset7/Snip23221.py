def test_optgroups_integer_choices(self):
        """The option 'value' is the same type as what's in `choices`."""
        groups = list(
            self.widget(choices=[[0, "choice text"]]).optgroups("name", ["vhs"])
        )
        label, options, index = groups[0]
        self.assertEqual(options[0]["value"], 0)