def get_joining_fields(self, reverse_join=False):
        return tuple(
            self.reverse_related_fields if reverse_join else self.related_fields
        )