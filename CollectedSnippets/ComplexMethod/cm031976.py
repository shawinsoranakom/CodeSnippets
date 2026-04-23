def is_fixed_type(vardecl):
    if not vardecl:
        return None
    _, _, _, typespec, abstract = _info.get_parsed_vartype(vardecl)
    if 'typeof' in typespec:
        raise NotImplementedError(vardecl)
    elif not abstract:
        return True

    if '*' not in abstract:
        # XXX What about []?
        return True
    elif _match._is_funcptr(abstract):
        return True
    else:
        for after in abstract.split('*')[1:]:
            if not after.lstrip().startswith('const'):
                return False
        else:
            return True