def __init__(self, fields=(), *args, **kwargs):
                fields = (
                    ChoiceField(label="Rank", choices=((1, 1), (2, 2))),
                    CharField(label="Name", max_length=10),
                )
                super().__init__(fields=fields, *args, **kwargs)