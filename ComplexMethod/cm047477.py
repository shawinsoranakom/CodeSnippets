def _search_related(self, records: BaseModel, operator: str, value) -> DomainType:
        """ Determine the domain to search on field ``self``. """

        # Compute the new domain for ('x.y.z', op, value)
        # as ('x', 'any', [('y', 'any', [('z', op, value)])])
        # If the followed relation is a nullable many2one, we accept null
        # for that path as well.

        # determine whether the related field can be null
        falsy_value = self.falsy_value
        if isinstance(value, COLLECTION_TYPES):
            value_is_null = any(val is False or val is None or val == falsy_value for val in value)
        else:
            value_is_null = value is False or value is None or value == falsy_value
        can_be_null = (  # (..., '=', False) or (..., 'not in', [truthy vals])
            (operator not in Domain.NEGATIVE_OPERATORS) == value_is_null
        )
        if operator in Domain.NEGATIVE_OPERATORS and not value_is_null:
            # we have a condition like 'not in' ['a']
            # let's call back with a positive operator
            return NotImplemented

        # parse the path
        field_seq = []
        model_name = self.model_name
        for fname in self.related.split('.'):
            field = records.env[model_name]._fields[fname]
            field_seq.append(field)
            model_name = field.comodel_name

        # build the domain backwards with the any operator
        domain = Domain(field_seq[-1].name, operator, value)
        for field in reversed(field_seq[:-1]):
            domain = Domain(field.name, 'any!' if self.compute_sudo else 'any', domain)
            if can_be_null and field.type == 'many2one' and not field.required:
                domain |= Domain(field.name, '=', False)
        return domain