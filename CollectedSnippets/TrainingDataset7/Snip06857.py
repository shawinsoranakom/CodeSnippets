def add_item_elements(self, handler, item):
        super().add_item_elements(handler, item)
        self.add_georss_element(handler, item)