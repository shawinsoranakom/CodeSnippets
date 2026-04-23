def add_root_elements(self, handler):
        handler.addQuickElement("title", self.feed["title"])
        handler.addQuickElement(
            "link", "", {"rel": "alternate", "href": self.feed["link"]}
        )
        if self.feed["feed_url"] is not None:
            handler.addQuickElement(
                "link", "", {"rel": "self", "href": self.feed["feed_url"]}
            )
        handler.addQuickElement("id", self.feed["id"])
        handler.addQuickElement("updated", rfc3339_date(self.latest_post_date()))
        if self.feed["author_name"] is not None:
            handler.startElement("author", {})
            handler.addQuickElement("name", self.feed["author_name"])
            if self.feed["author_email"] is not None:
                handler.addQuickElement("email", self.feed["author_email"])
            if self.feed["author_link"] is not None:
                handler.addQuickElement("uri", self.feed["author_link"])
            handler.endElement("author")
        if self.feed["subtitle"] is not None:
            handler.addQuickElement("subtitle", self.feed["subtitle"])
        for cat in self.feed["categories"]:
            handler.addQuickElement("category", "", {"term": cat})
        if self.feed["feed_copyright"] is not None:
            handler.addQuickElement("rights", self.feed["feed_copyright"])