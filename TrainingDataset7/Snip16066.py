def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically add a field with optgroups after instantiation.
        self.fields["articles"] = forms.ChoiceField(
            choices=[
                ("Category A", [("1", "Item 1"), ("2", "Item 2")]),
                ("Category B", [("3", "Item 3"), ("4", "Item 4")]),
            ],
            required=False,
        )