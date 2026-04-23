def add_root_elements(self, handler):
        super().add_root_elements(handler)
        self.add_georss_element(handler, self.feed, w3c_geo=True)