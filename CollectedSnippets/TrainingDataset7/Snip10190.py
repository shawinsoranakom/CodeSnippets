def __eq__(self, other):
        return (
            isinstance(other, Migration)
            and self.name == other.name
            and self.app_label == other.app_label
        )