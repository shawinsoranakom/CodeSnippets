def _optimize_field_search_method(self, model: BaseModel) -> Domain:
        field = self._field(model)
        operator, value = self.operator, self.value
        # use the `Field.search` function
        original_exception = None
        try:
            computed_domain = field.determine_domain(model, operator, value)
        except (NotImplementedError, UserError) as e:
            computed_domain = NotImplemented
            original_exception = e
        else:
            if computed_domain is not NotImplemented:
                return Domain(computed_domain, internal=True)
        # try with the positive operator
        if (
            original_exception is None
            and (inversed_opeator := _INVERSE_OPERATOR.get(operator))
        ):
            computed_domain = field.determine_domain(model, inversed_opeator, value)
            if computed_domain is not NotImplemented:
                return ~Domain(computed_domain, internal=True)
        # compatibility for any!
        try:
            if operator in ('any!', 'not any!'):
                # Not strictly equivalent! If a search is executed, it will be done using sudo.
                computed_domain = DomainCondition(self.field_expr, operator.rstrip('!'), value)
                computed_domain = computed_domain._optimize_field_search_method(model.sudo())
                _logger.warning("Field %s should implement any! operator", field)
                return computed_domain
        except (NotImplementedError, UserError) as e:
            if original_exception is None:
                original_exception = e
        # backward compatibility to implement only '=' or '!='
        try:
            if operator == 'in':
                return Domain.OR(Domain(field.determine_domain(model, '=', v), internal=True) for v in value)
            elif operator == 'not in':
                return Domain.AND(Domain(field.determine_domain(model, '!=', v), internal=True) for v in value)
        except (NotImplementedError, UserError) as e:
            if original_exception is None:
                original_exception = e
        # raise the error
        if original_exception:
            raise original_exception
        raise UserError(model.env._(
            "Unsupported operator on %(field_label)s %(model_label)s in %(domain)s",
            domain=repr(self),
            field_label=self._field(model).get_description(model.env, ['string'])['string'],
            model_label=f"{model.env['ir.model']._get(model._name).name!r} ({model._name})",
        ))