def _parse_alias(self, alias):
        name, value = alias.split("\t", 1)
        return name, value