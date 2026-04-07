def write_items(self, handler):
        for item in self.items:
            handler.startElement("item", self.item_attributes(item))
            self.add_item_elements(handler, item)
            handler.endElement("item")