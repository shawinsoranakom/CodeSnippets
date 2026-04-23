def get_globals_in_pkl(file) -> set[str]:
    globals_in_checkpoint = set()
    read = file.read
    readline = file.readline
    op_to_bytes_to_read = {
        NEWOBJ[0]: 0,
        REDUCE[0]: 0,
        BUILD[0]: 0,
        APPEND[0]: 0,
        APPENDS[0]: 0,
        SETITEM[0]: 0,
        SETITEMS[0]: 0,
        MARK[0]: 0,
        TUPLE[0]: 0,
        TUPLE1[0]: 0,
        TUPLE2[0]: 0,
        TUPLE3[0]: 0,
        NONE[0]: 0,
        NEWFALSE[0]: 0,
        NEWTRUE[0]: 0,
        EMPTY_TUPLE[0]: 0,
        EMPTY_LIST[0]: 0,
        EMPTY_DICT[0]: 0,
        EMPTY_SET[0]: 0,
        BINPERSID[0]: 0,
        BININT[0]: 4,
        BININT1[0]: 1,
        BININT2[0]: 2,
        BINFLOAT[0]: 8,
        BINGET[0]: 1,
        LONG_BINGET[0]: 4,
        BINPUT[0]: 1,
        LONG_BINPUT[0]: 4,
    }
    while True:
        key = read(1)
        if not key:
            raise EOFError
        if not isinstance(key, bytes_types):
            raise AssertionError(f"Expected bytes, got {type(key).__name__}")
        if key[0] == GLOBAL[0]:
            module, name = _read_global_instruction(readline)
            globals_in_checkpoint.add(f"{module}.{name}")
        elif key[0] in op_to_bytes_to_read:
            bytes_to_read = op_to_bytes_to_read[key[0]]
            if bytes_to_read:
                read(bytes_to_read)
        # ops where bytes to read depends on the data
        elif key[0] == BINUNICODE[0]:
            strlen = unpack("<I", read(4))[0]
            if strlen > maxsize:
                raise UnpicklingError("String is too long")
            read(strlen)
        elif key[0] in {SHORT_BINSTRING[0], LONG1[0]}:
            strlen = read(1)[0]
            read(strlen)
        # first and last op
        elif key[0] == PROTO[0]:
            read(1)[0]
        elif key[0] == STOP[0]:
            return globals_in_checkpoint
        else:
            raise UnpicklingError(f"Unsupported operand {key[0]}")