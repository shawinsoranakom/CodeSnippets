def media(self):
        """Return all media required to render the widgets on this form."""
        media = Media()
        for field in self.fields.values():
            media += field.widget.media
        return media