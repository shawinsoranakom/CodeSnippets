def _handle_unresolved(unresolved, types, analyze_decl):
    #raise NotImplementedError(unresolved)

    dump = True
    dump = False
    if dump:
        print()
    for decl in types:  # Preserve the original order.
        if decl not in unresolved:
            assert types[decl] is not None, decl
            if types[decl] in (UNKNOWN, IGNORED):
                unresolved.add(decl)
                if dump:
                    _dump_unresolved(decl, types, analyze_decl)
                    print()
            else:
                assert types[decl][0] is not None, (decl, types[decl])
                assert None not in types[decl][0], (decl, types[decl])
        else:
            assert types[decl] is None
            if dump:
                _dump_unresolved(decl, types, analyze_decl)
                print()
    #raise NotImplementedError

    for decl in unresolved:
        types[decl] = ([_SKIPPED], None)

    for decl in types:
        assert types[decl]