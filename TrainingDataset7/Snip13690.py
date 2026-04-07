def __eq__(self, element):
        if not hasattr(element, "name") or self.name != element.name:
            return False
        if self.attributes != element.attributes:
            return False
        return self.children == element.children