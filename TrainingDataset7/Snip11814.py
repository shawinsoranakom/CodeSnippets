def process_rhs(self, qn, connection):
        rhs, params = super().process_rhs(qn, connection)
        # Assume the lookup is startswith. For simple lookups involving a
        # Python value like "thevalue", the (SQL, params) is something like:
        #     ("col LIKE %s", ['thevalue%'])
        if self.is_simple_lookup:
            # Prepare the lookup parameter, a Python value, for use in a LIKE
            # clause, usually by adding % signs to the beginning and/or end of
            # the value.
            param = connection.ops.prep_for_like_query(params[0])
            if connection.features.pattern_lookup_needs_param_pattern:
                param = self.param_pattern % param
            params = (param, *params[1:])
        return rhs, params