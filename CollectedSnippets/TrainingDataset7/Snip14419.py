def add_item_elements(self, handler, item):
        handler.addQuickElement("title", item["title"])
        handler.addQuickElement("link", item["link"])
        if item["description"] is not None:
            handler.addQuickElement("description", item["description"])