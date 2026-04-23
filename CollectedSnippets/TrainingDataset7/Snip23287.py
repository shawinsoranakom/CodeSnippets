def __init__(self, choices=[]):
        widgets = [
            RadioSelect(choices=choices),
            TextInput,
        ]
        super().__init__(widgets)