def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use Section instances as optgroup keys
        sections = Section.objects.all()[:2]
        if sections:
            self.fields["articles"].choices = [
                (sections[0], [("1", "Article 1")]),
                (
                    sections[1] if len(sections) > 1 else sections[0],
                    [("2", "Article 2")],
                ),
            ]