def _dump_unresolved(decl, types, analyze_decl):
    if isinstance(decl, str):
        typespec = decl
        decl, = (d for d in types if d.shortkey == typespec)
    elif type(decl) is tuple:
        filename, typespec = decl
        if '-' in typespec:
            found = [d for d in types
                     if d.shortkey == typespec and d.filename == filename]
            #if not found:
            #    raise NotImplementedError(decl)
            decl, = found
        else:
            found = [d for d in types if d.shortkey == typespec]
            if not found:
                print(f'*** {typespec} ???')
                return
                #raise NotImplementedError(decl)
            else:
                decl, = found
    resolved = analyze_decl(decl)
    if resolved:
        typedeps, _ = resolved or (None, None)

    if decl.kind is KIND.STRUCT or decl.kind is KIND.UNION:
        print(f'*** {decl.shortkey} {decl.filename}')
        for member, mtype in zip(decl.members, typedeps):
            typespec = member.vartype.typespec
            if typespec == decl.shortkey:
                print(f'     ~~~~: {typespec:20} - {member!r}')
                continue
            status = None
            if is_pots(typespec):
                mtype = typespec
                status = 'okay'
            elif is_system_type(typespec):
                mtype = typespec
                status = 'okay'
            elif mtype is None:
                if '-' in member.vartype.typespec:
                    mtype, = [d for d in types
                              if d.shortkey == member.vartype.typespec
                              and d.filename == decl.filename]
                else:
                    found = [d for d in types
                             if d.shortkey == typespec]
                    if not found:
                        print(f' ???: {typespec:20}')
                        continue
                    mtype, = found
            if status is None:
                status = 'okay' if types.get(mtype) else 'oops'
            if mtype is _SKIPPED:
                status = 'okay'
                mtype = '<skipped>'
            elif isinstance(mtype, FuncPtr):
                status = 'okay'
                mtype = str(mtype.vartype)
            elif not isinstance(mtype, str):
                if hasattr(mtype, 'vartype'):
                    if is_funcptr(mtype.vartype):
                        status = 'okay'
                mtype = str(mtype).rpartition('(')[0].rstrip()
            status = '    okay' if status == 'okay' else f'--> {status}'
            print(f' {status}: {typespec:20} - {member!r} ({mtype})')
    else:
        print(f'*** {decl} ({decl.vartype!r})')
        if decl.vartype.typespec.startswith('struct ') or is_funcptr(decl):
            _dump_unresolved(
                (decl.filename, decl.vartype.typespec),
                types,
                analyze_decl,
            )