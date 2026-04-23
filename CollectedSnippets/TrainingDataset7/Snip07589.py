def tags(self):
        return " ".join(tag for tag in [self.extra_tags, self.level_tag] if tag)