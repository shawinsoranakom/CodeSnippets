def get_extra_restriction(self, alias, related_alias):
        return ColConstraint(alias, "lang", get_language())