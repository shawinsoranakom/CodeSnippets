def _compile(code, pattern, flags):
    # internal: compile a (sub)pattern
    emit = code.append
    _len = len
    LITERAL_CODES = _LITERAL_CODES
    REPEATING_CODES = _REPEATING_CODES
    SUCCESS_CODES = _SUCCESS_CODES
    ASSERT_CODES = _ASSERT_CODES
    iscased = None
    tolower = None
    fixes = None
    if flags & SRE_FLAG_IGNORECASE and not flags & SRE_FLAG_LOCALE:
        if flags & SRE_FLAG_UNICODE:
            iscased = _sre.unicode_iscased
            tolower = _sre.unicode_tolower
            fixes = _EXTRA_CASES
        else:
            iscased = _sre.ascii_iscased
            tolower = _sre.ascii_tolower
    for op, av in pattern:
        if op in LITERAL_CODES:
            if not flags & SRE_FLAG_IGNORECASE:
                emit(op)
                emit(av)
            elif flags & SRE_FLAG_LOCALE:
                emit(OP_LOCALE_IGNORE[op])
                emit(av)
            elif not iscased(av):
                emit(op)
                emit(av)
            else:
                lo = tolower(av)
                if not fixes:  # ascii
                    emit(OP_IGNORE[op])
                    emit(lo)
                elif lo not in fixes:
                    emit(OP_UNICODE_IGNORE[op])
                    emit(lo)
                else:
                    emit(IN_UNI_IGNORE)
                    skip = _len(code); emit(0)
                    if op is NOT_LITERAL:
                        emit(NEGATE)
                    for k in (lo,) + fixes[lo]:
                        emit(LITERAL)
                        emit(k)
                    emit(FAILURE)
                    code[skip] = _len(code) - skip
        elif op is IN:
            charset, hascased = _optimize_charset(av, iscased, tolower, fixes)
            if not charset:
                emit(FAILURE)
            elif charset == _CHARSET_ALL:
                emit(ANY_ALL)
            else:
                if flags & SRE_FLAG_IGNORECASE and flags & SRE_FLAG_LOCALE:
                    emit(IN_LOC_IGNORE)
                elif not hascased:
                    emit(IN)
                elif not fixes:  # ascii
                    emit(IN_IGNORE)
                else:
                    emit(IN_UNI_IGNORE)
                skip = _len(code); emit(0)
                _compile_charset(charset, flags, code)
                code[skip] = _len(code) - skip
        elif op is ANY:
            if flags & SRE_FLAG_DOTALL:
                emit(ANY_ALL)
            else:
                emit(ANY)
        elif op in REPEATING_CODES:
            if _simple(av[2]):
                emit(REPEATING_CODES[op][2])
                skip = _len(code); emit(0)
                emit(av[0])
                emit(av[1])
                _compile(code, av[2], flags)
                emit(SUCCESS)
                code[skip] = _len(code) - skip
            else:
                emit(REPEATING_CODES[op][0])
                skip = _len(code); emit(0)
                emit(av[0])
                emit(av[1])
                _compile(code, av[2], flags)
                code[skip] = _len(code) - skip
                emit(REPEATING_CODES[op][1])
        elif op is SUBPATTERN:
            group, add_flags, del_flags, p = av
            if group:
                emit(MARK)
                emit((group-1)*2)
            # _compile_info(code, p, _combine_flags(flags, add_flags, del_flags))
            _compile(code, p, _combine_flags(flags, add_flags, del_flags))
            if group:
                emit(MARK)
                emit((group-1)*2+1)
        elif op is ATOMIC_GROUP:
            # Atomic Groups are handled by starting with an Atomic
            # Group op code, then putting in the atomic group pattern
            # and finally a success op code to tell any repeat
            # operations within the Atomic Group to stop eating and
            # pop their stack if they reach it
            emit(ATOMIC_GROUP)
            skip = _len(code); emit(0)
            _compile(code, av, flags)
            emit(SUCCESS)
            code[skip] = _len(code) - skip
        elif op in SUCCESS_CODES:
            emit(op)
        elif op in ASSERT_CODES:
            emit(op)
            skip = _len(code); emit(0)
            if av[0] >= 0:
                emit(0) # look ahead
            else:
                lo, hi = av[1].getwidth()
                if lo > MAXCODE:
                    raise error("looks too much behind")
                if lo != hi:
                    raise PatternError("look-behind requires fixed-width pattern")
                emit(lo) # look behind
            _compile(code, av[1], flags)
            emit(SUCCESS)
            code[skip] = _len(code) - skip
        elif op is AT:
            emit(op)
            if flags & SRE_FLAG_MULTILINE:
                av = AT_MULTILINE.get(av, av)
            if flags & SRE_FLAG_LOCALE:
                av = AT_LOCALE.get(av, av)
            elif flags & SRE_FLAG_UNICODE:
                av = AT_UNICODE.get(av, av)
            emit(av)
        elif op is BRANCH:
            emit(op)
            tail = []
            tailappend = tail.append
            for av in av[1]:
                skip = _len(code); emit(0)
                # _compile_info(code, av, flags)
                _compile(code, av, flags)
                emit(JUMP)
                tailappend(_len(code)); emit(0)
                code[skip] = _len(code) - skip
            emit(FAILURE) # end of branch
            for tail in tail:
                code[tail] = _len(code) - tail
        elif op is CATEGORY:
            emit(op)
            if flags & SRE_FLAG_LOCALE:
                av = CH_LOCALE[av]
            elif flags & SRE_FLAG_UNICODE:
                av = CH_UNICODE[av]
            emit(av)
        elif op is GROUPREF:
            if not flags & SRE_FLAG_IGNORECASE:
                emit(op)
            elif flags & SRE_FLAG_LOCALE:
                emit(GROUPREF_LOC_IGNORE)
            elif not fixes:  # ascii
                emit(GROUPREF_IGNORE)
            else:
                emit(GROUPREF_UNI_IGNORE)
            emit(av-1)
        elif op is GROUPREF_EXISTS:
            emit(op)
            emit(av[0]-1)
            skipyes = _len(code); emit(0)
            _compile(code, av[1], flags)
            if av[2]:
                emit(JUMP)
                skipno = _len(code); emit(0)
                code[skipyes] = _len(code) - skipyes + 1
                _compile(code, av[2], flags)
                code[skipno] = _len(code) - skipno
            else:
                code[skipyes] = _len(code) - skipyes + 1
        else:
            raise PatternError(f"internal: unsupported operand type {op!r}")