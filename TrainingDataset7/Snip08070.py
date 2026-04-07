def __init__(self, info_dict, priority=None, changefreq=None, protocol=None):
        self.queryset = info_dict["queryset"]
        self.date_field = info_dict.get("date_field")
        self.priority = self.priority or priority
        self.changefreq = self.changefreq or changefreq
        self.protocol = self.protocol or protocol