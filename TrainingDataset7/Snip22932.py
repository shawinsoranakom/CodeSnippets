def __init__(self, fields=(), *args, **kwargs):
                fields = (
                    CharField(label="First name", max_length=10),
                    CharField(label="Last name", max_length=10),
                )
                super().__init__(fields=fields, *args, **kwargs)