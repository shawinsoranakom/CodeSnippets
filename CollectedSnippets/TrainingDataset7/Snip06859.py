def root_attributes(self):
        attrs = super().root_attributes()
        attrs["xmlns:georss"] = "http://www.georss.org/georss"
        return attrs