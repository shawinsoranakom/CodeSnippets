def get_group_by_cols(self, wrapper=None):
        # If wrapper is referenced by an alias for an explicit GROUP BY through
        # values() a reference to this expression and not the self must be
        # returned to ensure external column references are not grouped against
        # as well.
        external_cols = self.get_external_cols()
        if any(col.possibly_multivalued for col in external_cols):
            return [wrapper or self]
        return external_cols