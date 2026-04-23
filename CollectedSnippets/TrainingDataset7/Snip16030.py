def get_urls(self):
        # Corner case: Don't call parent implementation
        return [path("extra/", self.extra, name="cable_extra")]