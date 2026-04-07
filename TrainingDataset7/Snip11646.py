def get_prep_lookup(self):
        if self.rhs_is_direct_value():
            self.check_rhs_is_tuple_or_list()
            self.check_rhs_is_collection_of_tuples_or_lists()
            self.check_rhs_elements_length_equals_lhs_length()
        else:
            self.check_rhs_is_query()
            super(TupleLookupMixin, self).get_prep_lookup()

        return self.rhs