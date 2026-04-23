def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self._trailing_slash_required():
            self.fields["url"].help_text = _(
                "Example: “/about/contact”. Make sure to have a leading slash."
            )