def media(self):
        media = self.opts.media + self.formset.media
        for fs in self:
            media += fs.media
        return media