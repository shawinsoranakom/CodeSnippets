def enhance_signature_using_docstring(signature, method):
    docstring = inspect.cleandoc(method.__doc__)
    doctree = _DocUtils.tree(docstring)

    # extract the ":param [annotation] <name>: text" and alike fields
    # from the docstring
    field_lists = [node for node in doctree if node.tagname in ('docinfo', 'field_list')]
    for field_list in field_lists:
        for field in field_list:
            field_name, field_body = field.children
            kind, _, name = str(field_name[0]).partition(' ')
            match (RST_INFO_FIELDS.get(kind), name.strip()):
                # unrecognized kind, e.g. var, meta, ...
                case (None, _):
                    pass
                # :param <annotation> <name>: <rst>
                case ('param', annotation_name) if ' ' in annotation_name:
                    annotation, _, name = annotation_name.rpartition(' ')
                    if param := signature.parameters.get(name.strip()):
                        if not param.annotation:
                            param.annotation = annotation.strip()
                        param.doc = _DocUtils.html_children(field_body)
                # :param <name>: <rst>
                case ('param', name):
                    if param := signature.parameters.get(name):
                        param.doc = _DocUtils.html_children(field_body)
                # :type <name>: <annotation>
                case ('type', name):
                    if (param := signature.parameters.get(name)) and not param.annotation:
                        param.annotations = field_body.children[0].astext().strip()
                # :returns: <rst>
                case ('returns', ''):
                    signature.return_.doc = _DocUtils.html_children(field_body)
                # :rtype: <annotation>
                case ('rtype', ''):
                    if not signature.return_.annotation:
                        signature.return_.annotation = field_body.children[0].astext().strip()
                # :raises <exception>: <rst>
                case ('raises', exception):
                    signature.raise_[exception] = _DocUtils.html_children(field_body)
                case _:
                    logger.warning(RST_PARSE_ERROR.format(docstring, f"cannot parse {field_name[0]}"))
        doctree.remove(field_list)

    signature.doc = _DocUtils.html(doctree)