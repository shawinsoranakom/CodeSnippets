def _combine_sql_parts(self, parts):
        # Add condition for each key.
        if self.logical_operator:
            return "(%s)" % self.logical_operator.join(parts)
        return "".join(parts)