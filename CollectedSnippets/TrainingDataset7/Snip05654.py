def media(self):
        media = self.form.media
        for fs in self:
            media += fs.media
        return media