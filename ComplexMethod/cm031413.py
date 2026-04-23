def _compile_charset(charset, flags, code):
    # compile charset subprogram
    emit = code.append
    for op, av in charset:
        emit(op)
        if op is NEGATE:
            pass
        elif op is LITERAL:
            emit(av)
        elif op is RANGE or op is RANGE_UNI_IGNORE:
            emit(av[0])
            emit(av[1])
        elif op is CHARSET:
            code.extend(av)
        elif op is BIGCHARSET:
            code.extend(av)
        elif op is CATEGORY:
            if flags & SRE_FLAG_LOCALE:
                emit(CH_LOCALE[av])
            elif flags & SRE_FLAG_UNICODE:
                emit(CH_UNICODE[av])
            else:
                emit(av)
        else:
            raise PatternError(f"internal: unsupported set operator {op!r}")
    emit(FAILURE)