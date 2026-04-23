def _as_predicate(self, records):
        if not records:
            return lambda _: False

        if self._opt_level < OptimizationLevel.DYNAMIC_VALUES:
            return self._optimize(records, OptimizationLevel.DYNAMIC_VALUES)._as_predicate(records)

        operator = self.operator
        if operator in ('child_of', 'parent_of'):
            # TODO have a specific implementation for these
            return self._optimize(records, OptimizationLevel.FULL)._as_predicate(records)

        assert operator in STANDARD_CONDITION_OPERATORS, "Expecting a sub-set of operators"
        field_expr, value = self.field_expr, self.value
        positive_operator = NEGATIVE_CONDITION_OPERATORS.get(operator, operator)

        if isinstance(value, SQL):
            # transform into an Query value
            if positive_operator == operator:
                condition = self
                operator = 'any!'
            else:
                condition = ~self
                operator = 'not any!'
            positive_operator = 'any!'
            field_expr = 'id'
            value = records.with_context(active_test=False)._search(DomainCondition('id', 'in', OrderedSet(records.ids)) & condition)
            assert isinstance(value, Query)

        if isinstance(value, Query):
            # rebuild a domain with an 'in' values
            if positive_operator not in ('in', 'any', 'any!'):
                self._raise("Cannot filter using Query without the 'any' or 'in' operator")
            if positive_operator != 'in':
                operator = 'in' if positive_operator == operator else 'not in'
                positive_operator = 'in'
            value = set(value.get_result_ids())
            return DomainCondition(field_expr, operator, value)._as_predicate(records)

        field = self._field(records)
        if field_expr == 'display_name':
            # when searching by name, ignore AccessError
            field_expr = 'display_name.no_error'
        elif field_expr == 'id':
            # for new records, compare to their origin
            field_expr = 'id.origin'

        func = field.filter_function(records, field_expr, positive_operator, value)
        return func if positive_operator == operator else lambda rec: not func(rec)