def __init__(self, fields=(), *args, **kwargs):
                fields = (DateField(label="Date"), IntegerField(label="Age"))
                super().__init__(fields=fields, *args, **kwargs)