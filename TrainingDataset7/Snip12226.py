def _get_col(self, target, field, alias):
        if not self.alias_cols:
            alias = None
        return target.get_col(alias, field)