def locate_node(arch, spec):
    """ Locate a node in a source (parent) architecture.

    Given a complete source (parent) architecture (i.e. the field
    `arch` in a view), and a 'spec' node (a node in an inheriting
    view that specifies the location in the source view of what
    should be changed), return (if it exists) the node in the
    source view matching the specification.

    :param arch: a parent architecture to modify
    :param spec: a modifying node in an inheriting view
    :return: a node in the source matching the spec
    """
    if spec.tag == 'xpath':
        expr = spec.get('expr')
        if expr is None:
            raise ValidationError(_lt("Missing 'expr' attribute in xpath specification"))
        try:
            xPath = etree.ETXPath(expr)
        except etree.XPathSyntaxError as e:
            raise ValidationError(_lt("Invalid Expression while parsing xpath “%s”", expr)) from e
        nodes = xPath(arch)
        return nodes[0] if nodes else None
    elif spec.tag == 'field':
        # Only compare the field name: a field can be only once in a given view
        # at a given level (and for multilevel expressions, we should use xpath
        # inheritance spec anyway).
        for node in arch.iter('field'):
            if node.get('name') == spec.get('name'):
                return node
        return None

    for node in arch.iter(spec.tag):
        if all(node.get(attr) == spec.get(attr) for attr in spec.attrib if attr != 'position'):
            return node
    return None