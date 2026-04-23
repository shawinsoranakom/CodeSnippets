def foreign_related_fields(self):
        return tuple(
            rhs_field for lhs_field, rhs_field in self.related_fields if rhs_field
        )