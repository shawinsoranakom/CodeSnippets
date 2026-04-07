def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields["character"].required = False