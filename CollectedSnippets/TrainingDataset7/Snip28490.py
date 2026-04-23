def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Allow archived authors.
                self.fields["writer"].queryset = Writer._base_manager.all()