def get_absolute_url(self):
        return "/title/%s/" % quote(self.title)