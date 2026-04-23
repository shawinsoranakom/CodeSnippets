def _operator_hierarchy(condition, model):
    """Transform a hierarchy operator into a simpler domain.

    ### Semantic of hierarchical operator: `(field, operator, value)`

    `field` is either 'id' to indicate to use the default parent relation (`_parent_name`)
    or it is a field where the comodel is the same as the model.
    The value is used to search a set of `related_records`. We start from the given value,
    which can be ids, a name (for searching by name), etc. Then we follow up the relation;
    forward in case of `parent_of` and backward in case of `child_of`.
    The resulting domain will have 'id' if the field is 'id' or a many2one.

    In the case where the comodel is not the same as the model, the result is equivalent to
    `('field', 'any', ('id', operator, value))`
    """
    if condition.operator == 'parent_of':
        hierarchy = _operator_parent_of_domain
    else:
        hierarchy = _operator_child_of_domain
    value = condition.value
    if value is False:
        return _FALSE_DOMAIN
    # Get:
    # - field: used in the resulting domain)
    # - parent (str | None): field name to find parent in the hierarchy
    # - comodel_sudo: used to resolve the hierarchy
    # - comodel: used to search for ids based on the value
    field = condition._field(model)
    if field.type == 'many2one':
        comodel = model.env[field.comodel_name].with_context(active_test=False)
    elif field.type in ('one2many', 'many2many'):
        comodel = model.env[field.comodel_name].with_context(**field.context)
    elif field.name == 'id':
        comodel = model
    else:
        condition._raise(f"Cannot execute {condition.operator} for {field}, works only for relational fields")
    comodel_sudo = comodel.sudo().with_context(active_test=False)
    parent = comodel._parent_name
    if comodel._name == model._name:
        if condition.field_expr != 'id':
            parent = condition.field_expr
        if field.type == 'many2one':
            field = model._fields['id']
    # Get the initial ids and bind them to comodel_sudo before resolving the hierarchy
    if isinstance(value, (int, str)):
        value = [value]
    elif not isinstance(value, COLLECTION_TYPES):
        condition._raise(f"Value of type {type(value)} is not supported")
    coids, other_values = partition(lambda v: isinstance(v, int), value)
    search_domain = _FALSE_DOMAIN
    if field.type == 'many2many':
        # always search for many2many
        search_domain |= DomainCondition('id', 'in', coids)
        coids = []
    if other_values:
        # search for strings
        search_domain |= Domain.OR(
            Domain('display_name', 'ilike', v)
            for v in other_values
        )
    coids += comodel.search(search_domain, order='id').ids
    if not coids:
        return _FALSE_DOMAIN
    result = hierarchy(comodel_sudo.browse(coids), parent)
    # Format the resulting domain
    if isinstance(result, Domain):
        if field.name == 'id':
            return result
        return DomainCondition(field.name, 'any!', result)
    return DomainCondition(field.name, 'in', result)