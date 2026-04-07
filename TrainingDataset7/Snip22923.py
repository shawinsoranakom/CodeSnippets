def __init__(self, names_required=False, *args, **kwargs):
                super().__init__(*args, **kwargs)

                if names_required:
                    self.fields["first_name"].required = True
                    self.fields["first_name"].widget.attrs["class"] = "required"
                    self.fields["last_name"].required = True
                    self.fields["last_name"].widget.attrs["class"] = "required"