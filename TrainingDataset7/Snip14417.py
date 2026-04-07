def add_root_elements(self, handler):
        handler.addQuickElement("title", self.feed["title"])
        handler.addQuickElement("link", self.feed["link"])
        handler.addQuickElement("description", self.feed["description"])
        if self.feed["feed_url"] is not None:
            handler.addQuickElement(
                "atom:link", None, {"rel": "self", "href": self.feed["feed_url"]}
            )
        if self.feed["language"] is not None:
            handler.addQuickElement("language", self.feed["language"])
        for cat in self.feed["categories"]:
            handler.addQuickElement("category", cat)
        if self.feed["feed_copyright"] is not None:
            handler.addQuickElement("copyright", self.feed["feed_copyright"])
        handler.addQuickElement("lastBuildDate", rfc2822_date(self.latest_post_date()))
        if self.feed["ttl"] is not None:
            handler.addQuickElement("ttl", self.feed["ttl"])