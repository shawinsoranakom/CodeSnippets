def handle_starttag(self, tag, attrs):
        self.output.append(self.get_starttag_text())
        if tag not in self.void_elements:
            self.tags.appendleft(tag)