def __init__(self, allow_unspec_gender=False, *args, **kwargs):
                super().__init__(*args, **kwargs)

                if allow_unspec_gender:
                    self.fields["gender"].choices += (("u", "Unspecified"),)