def order_to_function(order_part):
            order_match = regex_order.match(order_part)
            if not order_match:
                raise ValueError(f"Invalid order {order!r} to sort")
            field_name = order_match['field']
            property_name = order_match['property']
            reverse = (order_match['direction'] or '').upper() == 'DESC'
            nulls = (order_match['nulls'] or '').upper()
            if nulls:
                nulls_first = nulls == 'NULLS FIRST'
            else:
                nulls_first = reverse

            field = self._fields[field_name]
            field_expr = f'{field_name}.{property_name}' if property_name else field_name
            if field.type == 'many2one' and (not property_name or property_name == 'id'):
                seen = self.env.context.get('__m2o_order_seen_sorted', ())
                if field in seen:
                    return lambda _: None
                comodel = self.env[field.comodel_name].with_context(__m2o_order_seen_sorted=frozenset((field, *seen)))
                func_comodel = comodel._sorted_order_to_function(property_name or comodel._order)

                def getter(rec):
                    value = rec[field_name]
                    if not value:
                        return None
                    return func_comodel(value)
            elif field.relational:
                raise ValueError(f"Invalid order on relational field {order_part!r} to sort")
            elif field.type == 'boolean':
                getter = field.expression_getter(field_expr)
            else:
                raw_getter = field.expression_getter(field_expr)

                def getter(rec):
                    value = raw_getter(rec)
                    return value if value is not False else None

            comparator = functools.partial(
                ReversibleComparator,
                reverse=reverse,
                none_first=nulls_first,
            )
            return lambda rec: comparator(getter(rec))