def get_absolute_url(self):
        return "/users/%s/" % quote(self.name)