def handle_starttag(self, tag, attrs):
        attrs = normalize_attributes(attrs)
        element = Element(tag, attrs)
        self.current.append(element)
        if tag not in VOID_ELEMENTS:
            self.open_tags.append(element)
        self.element_positions[element] = self.getpos()