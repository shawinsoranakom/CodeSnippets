def get_groupby(view_tree, groupby=None, fields=None):
    """Parse the given groupby and fields and fallback to the view if not provided.

    Return the groupby as a list when given.
    Otherwise find groupby and fields from the view.

    :param view_tree: The xml tree of the view
    :param groupby: string or None
    :param fields: string or None
    """
    if groupby:
        groupby = groupby.split(',')
    if fields:
        fields = fields.split(',')
    else:
        fields = None
    if groupby is not None:
        return groupby, fields

    if view_tree.tag in ('pivot', 'graph'):
        # extract groupby from the view if we don't have any
        field_by_type = defaultdict(list)
        for element in view_tree.findall(r'./field'):
            field_name = element.attrib.get('name')
            if element.attrib.get('invisible', '') in ('1', 'true'):
                field_by_type['invisible'].append(field_name)
            else:
                field_by_type[element.attrib.get('type', 'normal')].append(field_name)
            # not reading interval from the attribute
        groupby = [
            *field_by_type.get('row', ()),
            *field_by_type.get('col', ()),
            *field_by_type.get('normal', ()),
        ]
        if fields is None:
            fields = field_by_type.get('measure', [])
        return groupby, fields
    if view_tree.attrib.get('default_group_by'):
        # in case the kanban view (or other) defines a default grouping
        # return the field name so it is added to the spec
        field = view_tree.attrib.get('default_group_by')
        return (None, [field] if field else [])
    return None, None