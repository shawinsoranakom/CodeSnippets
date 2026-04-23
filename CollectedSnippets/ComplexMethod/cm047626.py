def _optimize_step(self, model: BaseModel, level: OptimizationLevel) -> Domain:
        """Optimization step.

        Apply some generic optimizations and then dispatch optimizations
        according to the operator and the type of the field.
        Optimize recursively until a fixed point is found.

        - Validate the field.
        - Decompose *paths* into domains using 'any'.
        - If the field is *not stored*, run the search function of the field.
        - Run optimizations.
        - Check the output.
        """
        assert level is self._opt_level.next_level, f"Trying to skip optimization level after {self._opt_level}"

        if level == OptimizationLevel.BASIC:
            # optimize path
            field, property_name = self.__get_field(model)
            if property_name and field.relational:
                sub_domain = DomainCondition(property_name, self.operator, self.value)
                return DomainCondition(field.name, 'any', sub_domain)
        else:
            field = self._field(model)

        if level == OptimizationLevel.FULL:
            # resolve inherited fields
            # inherits implies both Field.delegate=True and Field.bypass_search_access=True
            # so no additional permissions will be added by the 'any' operator below
            if field.inherited:
                assert field.related
                parent_fname = field.related.split('.')[0]
                parent_domain = DomainCondition(self.field_expr, self.operator, self.value)
                return DomainCondition(parent_fname, 'any', parent_domain)

            # handle searchable fields
            if field.search and field.name == self.field_expr:
                domain = self._optimize_field_search_method(model)
                # The domain is optimized so that value data types are comparable.
                # Only simple optimization to avoid endless recursion.
                domain = domain.optimize(model)
                if domain != self:
                    return domain

        # apply optimizations of the level for operator and type
        optimizations = _OPTIMIZATIONS_FOR[level]
        for opt in optimizations.get(self.operator, ()):
            domain = opt(self, model)
            if domain != self:
                return domain
        for opt in optimizations.get(field.type, ()):
            domain = opt(self, model)
            if domain != self:
                return domain

        # final checks
        if self.operator not in STANDARD_CONDITION_OPERATORS and level == OptimizationLevel.FULL:
            self._raise("Not standard operator left")

        return self