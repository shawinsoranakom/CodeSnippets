def item_enclosures(self, item):
        return [
            feedgenerator.Enclosure("http://example.com/hello.png", "0", "image/png"),
            feedgenerator.Enclosure("http://example.com/goodbye.png", "0", "image/png"),
        ]