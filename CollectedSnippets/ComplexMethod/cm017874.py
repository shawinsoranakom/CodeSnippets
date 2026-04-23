def add_item_elements(self, handler, item):
        handler.addQuickElement("title", item["title"])
        handler.addQuickElement("link", "", {"href": item["link"], "rel": "alternate"})

        if item["pubdate"] is not None:
            handler.addQuickElement("published", rfc3339_date(item["pubdate"]))

        if item["updateddate"] is not None:
            handler.addQuickElement("updated", rfc3339_date(item["updateddate"]))

        # Author information.
        if item["author_name"] is not None:
            handler.startElement("author", {})
            handler.addQuickElement("name", item["author_name"])
            if item["author_email"] is not None:
                handler.addQuickElement("email", item["author_email"])
            if item["author_link"] is not None:
                handler.addQuickElement("uri", item["author_link"])
            handler.endElement("author")

        # Unique ID.
        if item["unique_id"] is not None:
            unique_id = item["unique_id"]
        else:
            unique_id = get_tag_uri(item["link"], item["pubdate"])
        handler.addQuickElement("id", unique_id)

        # Summary.
        if item["description"] is not None:
            handler.addQuickElement("summary", item["description"], {"type": "html"})

        # Enclosures.
        for enclosure in item["enclosures"]:
            handler.addQuickElement(
                "link",
                "",
                {
                    "rel": "enclosure",
                    "href": enclosure.url,
                    "length": enclosure.length,
                    "type": enclosure.mime_type,
                },
            )

        # Categories.
        for cat in item["categories"]:
            handler.addQuickElement("category", "", {"term": cat})

        # Rights.
        if item["item_copyright"] is not None:
            handler.addQuickElement("rights", item["item_copyright"])