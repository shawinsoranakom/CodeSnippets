def _optimize_properties_date_datetime(condition, model):
    operator = condition.operator
    if (
        operator not in ('in', 'not in', '>', '<', '<=', '>=')
        or condition.field_expr.count('.') != 1
        or not isinstance(condition.value, (str, OrderedSet))
    ):
        return condition
    definition = model.get_property_definition(condition.field_expr)
    property_type = definition.get("type")

    if property_type == 'date':
        value = _value_to_date(condition.value, model.env)
    elif property_type == 'datetime':
        value, _ = _value_to_datetime(condition.value, model.env)
    else:
        return condition
    # we need to serialize the value as a string to be able to use with properties
    if isinstance(value, COLLECTION_TYPES):
        value = OrderedSet(
            str(item) if isinstance(item, (date, datetime)) else item
            for item in value
        )
    elif isinstance(value, (date, datetime)):
        value = str(value)

    return DomainCondition(condition.field_expr, operator, value)