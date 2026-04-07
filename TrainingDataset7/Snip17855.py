def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields["groups"].help_text = (
                    "These groups give users different permissions"
                )