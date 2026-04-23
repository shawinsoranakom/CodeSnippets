def __init__(self, href, **attributes):
        super().__init__(href, **attributes)
        self.attributes["rel"] = "stylesheet"