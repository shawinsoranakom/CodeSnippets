def get_prep_lookup(self):
        if self.rhs_is_direct_value():
            self.check_rhs_is_tuple_or_list()
            self.check_rhs_length_equals_lhs_length()
        else:
            self.check_rhs_is_supported_expression()
            super().get_prep_lookup()
        return self.rhs