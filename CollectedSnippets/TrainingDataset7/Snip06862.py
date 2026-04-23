def rss_attributes(self):
        attrs = super().rss_attributes()
        attrs["xmlns:geo"] = "http://www.w3.org/2003/01/geo/wgs84_pos#"
        return attrs