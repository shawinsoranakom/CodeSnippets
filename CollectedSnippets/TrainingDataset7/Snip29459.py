def __eq__(self, other):
        return isinstance(other, Tag) and self.tag_id == other.tag_id