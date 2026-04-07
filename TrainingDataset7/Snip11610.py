def get_extra_restriction(self, alias, related_alias):
        return self.field.get_extra_restriction(related_alias, alias)