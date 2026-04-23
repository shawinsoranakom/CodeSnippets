def extract_docstring_params(doctree):
    params = {}  # sorted set
    types = {}
    rtype = inspect._empty

    field_lists = [node for node in doctree if node.tagname in ('docinfo', 'field_list')]
    for field_list in field_lists:
        for field in field_list:
            field_name, field_body = field.children
            kind, _, name = str(field_name[0]).partition(' ')
            if kind not in RST_INFO_FIELDS:
                e = f"unknown rst: {kind!r}\n{RST_INFO_FIELDS_DOC}"
                raise ValueError(e)
            kind = RST_INFO_FIELDS[kind]

            if kind == 'param':
                if not name:
                    e = "empty :param:"
                    raise ValueError(e)
                type_param, _, name = name.rpartition(' ')
                params[name] = None
                if type_param:
                    type_type = types.setdefault(name, type_param)
                    if type_type != type_param:
                        e = f"conflicting type: {type_param} (:param:) vs {type_type} (:type:)"
                        raise ValueError(e)

            elif kind == 'returns':
                if name:
                    e = f'invalid ":{kind} {name}:", did you mean ":rtype: {name}"?'
                    raise ValueError(e)

            elif kind == 'type':
                if not name:
                    e = "empty :type:"
                    raise ValueError(e)
                params[name] = None
                try:
                    type_type = field_body.children[0].astext().strip()
                except IndexError as exc:
                    if name:
                        e = f'invalid ":{kind} {name}:", did you mean ":{kind}: {name}"?'
                        raise ValueError(e) from exc
                    raise
                type_param = types.setdefault(name, type_type)
                if type_param != type_type:
                    e = f"conflicting type: {type_param} (:param:) vs {type_type} (:type:)"
                    raise ValueError(e)

            elif kind == 'rtype':
                try:
                    rtype = field_body.children[0].astext().strip()
                except IndexError as exc:
                    if name:
                        e = f'invalid ":{kind} {name}:", did you mean ":{kind}: {name}"?'
                        raise ValueError(e) from exc
                    raise

    return list(params), types, rtype