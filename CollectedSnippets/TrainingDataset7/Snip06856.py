def rss_attributes(self):
        attrs = super().rss_attributes()
        attrs["xmlns:georss"] = "http://www.georss.org/georss"
        return attrs