def __init__(self, name_max_length=None, *args, **kwargs):
                super().__init__(*args, **kwargs)

                if name_max_length:
                    self.fields["first_name"].max_length = name_max_length
                    self.fields["last_name"].max_length = name_max_length