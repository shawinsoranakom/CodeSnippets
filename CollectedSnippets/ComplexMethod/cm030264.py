def optimize(p):
    'Optimize a pickle string by removing unused PUT opcodes'
    put = 'PUT'
    get = 'GET'
    oldids = set()          # set of all PUT ids
    newids = {}             # set of ids used by a GET opcode
    opcodes = []            # (op, idx) or (pos, end_pos)
    proto = 0
    protoheader = b''
    for opcode, arg, pos, end_pos in _genops(p, yield_end_pos=True):
        if 'PUT' in opcode.name:
            oldids.add(arg)
            opcodes.append((put, arg))
        elif opcode.name == 'MEMOIZE':
            idx = len(oldids)
            oldids.add(idx)
            opcodes.append((put, idx))
        elif 'FRAME' in opcode.name:
            pass
        elif 'GET' in opcode.name:
            if opcode.proto > proto:
                proto = opcode.proto
            newids[arg] = None
            opcodes.append((get, arg))
        elif opcode.name == 'PROTO':
            if arg > proto:
                proto = arg
            if pos == 0:
                protoheader = p[pos:end_pos]
            else:
                opcodes.append((pos, end_pos))
        else:
            opcodes.append((pos, end_pos))
    del oldids

    # Copy the opcodes except for PUTS without a corresponding GET
    out = io.BytesIO()
    # Write the PROTO header before any framing
    out.write(protoheader)
    pickler = pickle._Pickler(out, proto)
    if proto >= 4:
        pickler.framer.start_framing()
    idx = 0
    for op, arg in opcodes:
        frameless = False
        if op is put:
            if arg not in newids:
                continue
            data = pickler.put(idx)
            newids[arg] = idx
            idx += 1
        elif op is get:
            data = pickler.get(newids[arg])
        else:
            data = p[op:arg]
            frameless = len(data) > pickler.framer._FRAME_SIZE_TARGET
        pickler.framer.commit_frame(force=frameless)
        if frameless:
            pickler.framer.file_write(data)
        else:
            pickler.write(data)
    pickler.framer.end_framing()
    return out.getvalue()