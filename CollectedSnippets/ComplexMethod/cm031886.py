def get_parsed_vartype(decl):
    kind = getattr(decl, 'kind', None)
    if isinstance(decl, ParsedItem):
        storage, vartype = _get_vartype(decl.data)
        typequal = vartype['typequal']
        typespec = vartype['typespec']
        abstract = vartype['abstract']
    elif isinstance(decl, dict):
        kind = decl.get('kind')
        storage, vartype = _get_vartype(decl)
        typequal = vartype['typequal']
        typespec = vartype['typespec']
        abstract = vartype['abstract']
    elif isinstance(decl, VarType):
        storage = None
        typequal, typespec, abstract = decl
    elif isinstance(decl, TypeDef):
        storage = None
        typequal, typespec, abstract = decl.vartype
    elif isinstance(decl, Variable):
        storage = decl.storage
        typequal, typespec, abstract = decl.vartype
    elif isinstance(decl, Signature):
        storage = None
        typequal, typespec, abstract = decl.returntype
    elif isinstance(decl, Function):
        storage = decl.storage
        typequal, typespec, abstract = decl.signature.returntype
    elif isinstance(decl, str):
        vartype, storage = VarType.from_str(decl)
        typequal, typespec, abstract = vartype
    else:
        raise NotImplementedError(decl)
    return kind, storage, typequal, typespec, abstract