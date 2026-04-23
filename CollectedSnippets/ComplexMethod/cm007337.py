def resfunc(args):
            # Helper functions
            coder = io.BytesIO(m.code)
            s24 = lambda: _s24(coder)
            u30 = lambda: _u30(coder)

            registers = [avm_class.variables] + list(args) + [None] * m.local_count
            stack = []
            scopes = collections.deque([
                self._classes_by_name, avm_class.constants, avm_class.variables])
            while True:
                opcode = _read_byte(coder)
                if opcode == 9:  # label
                    pass  # Spec says: "Do nothing."
                elif opcode == 16:  # jump
                    offset = s24()
                    coder.seek(coder.tell() + offset)
                elif opcode == 17:  # iftrue
                    offset = s24()
                    value = stack.pop()
                    if value:
                        coder.seek(coder.tell() + offset)
                elif opcode == 18:  # iffalse
                    offset = s24()
                    value = stack.pop()
                    if not value:
                        coder.seek(coder.tell() + offset)
                elif opcode == 19:  # ifeq
                    offset = s24()
                    value2 = stack.pop()
                    value1 = stack.pop()
                    if value2 == value1:
                        coder.seek(coder.tell() + offset)
                elif opcode == 20:  # ifne
                    offset = s24()
                    value2 = stack.pop()
                    value1 = stack.pop()
                    if value2 != value1:
                        coder.seek(coder.tell() + offset)
                elif opcode == 21:  # iflt
                    offset = s24()
                    value2 = stack.pop()
                    value1 = stack.pop()
                    if value1 < value2:
                        coder.seek(coder.tell() + offset)
                elif opcode == 32:  # pushnull
                    stack.append(None)
                elif opcode == 33:  # pushundefined
                    stack.append(undefined)
                elif opcode == 36:  # pushbyte
                    v = _read_byte(coder)
                    stack.append(v)
                elif opcode == 37:  # pushshort
                    v = u30()
                    stack.append(v)
                elif opcode == 38:  # pushtrue
                    stack.append(True)
                elif opcode == 39:  # pushfalse
                    stack.append(False)
                elif opcode == 40:  # pushnan
                    stack.append(float('NaN'))
                elif opcode == 42:  # dup
                    value = stack[-1]
                    stack.append(value)
                elif opcode == 44:  # pushstring
                    idx = u30()
                    stack.append(self.constant_strings[idx])
                elif opcode == 48:  # pushscope
                    new_scope = stack.pop()
                    scopes.append(new_scope)
                elif opcode == 66:  # construct
                    arg_count = u30()
                    args = list(reversed(
                        [stack.pop() for _ in range(arg_count)]))
                    obj = stack.pop()
                    res = obj.avm_class.make_object()
                    stack.append(res)
                elif opcode == 70:  # callproperty
                    index = u30()
                    mname = self.multinames[index]
                    arg_count = u30()
                    args = list(reversed(
                        [stack.pop() for _ in range(arg_count)]))
                    obj = stack.pop()

                    if obj == StringClass:
                        if mname == 'String':
                            assert len(args) == 1
                            assert isinstance(args[0], (
                                int, compat_str, _Undefined))
                            if args[0] == undefined:
                                res = 'undefined'
                            else:
                                res = compat_str(args[0])
                            stack.append(res)
                            continue
                        else:
                            raise NotImplementedError(
                                'Function String.%s is not yet implemented'
                                % mname)
                    elif isinstance(obj, _AVMClass_Object):
                        func = self.extract_function(obj.avm_class, mname)
                        res = func(args)
                        stack.append(res)
                        continue
                    elif isinstance(obj, _AVMClass):
                        func = self.extract_function(obj, mname)
                        res = func(args)
                        stack.append(res)
                        continue
                    elif isinstance(obj, _ScopeDict):
                        if mname in obj.avm_class.method_names:
                            func = self.extract_function(obj.avm_class, mname)
                            res = func(args)
                        else:
                            res = obj[mname]
                        stack.append(res)
                        continue
                    elif isinstance(obj, compat_str):
                        if mname == 'split':
                            assert len(args) == 1
                            assert isinstance(args[0], compat_str)
                            if args[0] == '':
                                res = list(obj)
                            else:
                                res = obj.split(args[0])
                            stack.append(res)
                            continue
                        elif mname == 'charCodeAt':
                            assert len(args) <= 1
                            idx = 0 if len(args) == 0 else args[0]
                            assert isinstance(idx, int)
                            res = ord(obj[idx])
                            stack.append(res)
                            continue
                    elif isinstance(obj, list):
                        if mname == 'slice':
                            assert len(args) == 1
                            assert isinstance(args[0], int)
                            res = obj[args[0]:]
                            stack.append(res)
                            continue
                        elif mname == 'join':
                            assert len(args) == 1
                            assert isinstance(args[0], compat_str)
                            res = args[0].join(obj)
                            stack.append(res)
                            continue
                    raise NotImplementedError(
                        'Unsupported property %r on %r'
                        % (mname, obj))
                elif opcode == 71:  # returnvoid
                    res = undefined
                    return res
                elif opcode == 72:  # returnvalue
                    res = stack.pop()
                    return res
                elif opcode == 73:  # constructsuper
                    # Not yet implemented, just hope it works without it
                    arg_count = u30()
                    args = list(reversed(
                        [stack.pop() for _ in range(arg_count)]))
                    obj = stack.pop()
                elif opcode == 74:  # constructproperty
                    index = u30()
                    arg_count = u30()
                    args = list(reversed(
                        [stack.pop() for _ in range(arg_count)]))
                    obj = stack.pop()

                    mname = self.multinames[index]
                    assert isinstance(obj, _AVMClass)

                    # We do not actually call the constructor for now;
                    # we just pretend it does nothing
                    stack.append(obj.make_object())
                elif opcode == 79:  # callpropvoid
                    index = u30()
                    mname = self.multinames[index]
                    arg_count = u30()
                    args = list(reversed(
                        [stack.pop() for _ in range(arg_count)]))
                    obj = stack.pop()
                    if isinstance(obj, _AVMClass_Object):
                        func = self.extract_function(obj.avm_class, mname)
                        res = func(args)
                        assert res is undefined
                        continue
                    if isinstance(obj, _ScopeDict):
                        assert mname in obj.avm_class.method_names
                        func = self.extract_function(obj.avm_class, mname)
                        res = func(args)
                        assert res is undefined
                        continue
                    if mname == 'reverse':
                        assert isinstance(obj, list)
                        obj.reverse()
                    else:
                        raise NotImplementedError(
                            'Unsupported (void) property %r on %r'
                            % (mname, obj))
                elif opcode == 86:  # newarray
                    arg_count = u30()
                    arr = []
                    for i in range(arg_count):
                        arr.append(stack.pop())
                    arr = arr[::-1]
                    stack.append(arr)
                elif opcode == 93:  # findpropstrict
                    index = u30()
                    mname = self.multinames[index]
                    for s in reversed(scopes):
                        if mname in s:
                            res = s
                            break
                    else:
                        res = scopes[0]
                    if mname not in res and mname in _builtin_classes:
                        stack.append(_builtin_classes[mname])
                    else:
                        stack.append(res[mname])
                elif opcode == 94:  # findproperty
                    index = u30()
                    mname = self.multinames[index]
                    for s in reversed(scopes):
                        if mname in s:
                            res = s
                            break
                    else:
                        res = avm_class.variables
                    stack.append(res)
                elif opcode == 96:  # getlex
                    index = u30()
                    mname = self.multinames[index]
                    for s in reversed(scopes):
                        if mname in s:
                            scope = s
                            break
                    else:
                        scope = avm_class.variables

                    if mname in scope:
                        res = scope[mname]
                    elif mname in _builtin_classes:
                        res = _builtin_classes[mname]
                    else:
                        # Assume uninitialized
                        # TODO warn here
                        res = undefined
                    stack.append(res)
                elif opcode == 97:  # setproperty
                    index = u30()
                    value = stack.pop()
                    idx = self.multinames[index]
                    if isinstance(idx, _Multiname):
                        idx = stack.pop()
                    obj = stack.pop()
                    obj[idx] = value
                elif opcode == 98:  # getlocal
                    index = u30()
                    stack.append(registers[index])
                elif opcode == 99:  # setlocal
                    index = u30()
                    value = stack.pop()
                    registers[index] = value
                elif opcode == 102:  # getproperty
                    index = u30()
                    pname = self.multinames[index]
                    if pname == 'length':
                        obj = stack.pop()
                        assert isinstance(obj, (compat_str, list))
                        stack.append(len(obj))
                    elif isinstance(pname, compat_str):  # Member access
                        obj = stack.pop()
                        if isinstance(obj, _AVMClass):
                            res = obj.static_properties[pname]
                            stack.append(res)
                            continue

                        assert isinstance(obj, (dict, _ScopeDict)), \
                            'Accessing member %r on %r' % (pname, obj)
                        res = obj.get(pname, undefined)
                        stack.append(res)
                    else:  # Assume attribute access
                        idx = stack.pop()
                        assert isinstance(idx, int)
                        obj = stack.pop()
                        assert isinstance(obj, list)
                        stack.append(obj[idx])
                elif opcode == 104:  # initproperty
                    index = u30()
                    value = stack.pop()
                    idx = self.multinames[index]
                    if isinstance(idx, _Multiname):
                        idx = stack.pop()
                    obj = stack.pop()
                    obj[idx] = value
                elif opcode == 115:  # convert_
                    value = stack.pop()
                    intvalue = int(value)
                    stack.append(intvalue)
                elif opcode == 128:  # coerce
                    u30()
                elif opcode == 130:  # coerce_a
                    value = stack.pop()
                    # um, yes, it's any value
                    stack.append(value)
                elif opcode == 133:  # coerce_s
                    assert isinstance(stack[-1], (type(None), compat_str))
                elif opcode == 147:  # decrement
                    value = stack.pop()
                    assert isinstance(value, int)
                    stack.append(value - 1)
                elif opcode == 149:  # typeof
                    value = stack.pop()
                    return {
                        _Undefined: 'undefined',
                        compat_str: 'String',
                        int: 'Number',
                        float: 'Number',
                    }[type(value)]
                elif opcode == 160:  # add
                    value2 = stack.pop()
                    value1 = stack.pop()
                    res = value1 + value2
                    stack.append(res)
                elif opcode == 161:  # subtract
                    value2 = stack.pop()
                    value1 = stack.pop()
                    res = value1 - value2
                    stack.append(res)
                elif opcode == 162:  # multiply
                    value2 = stack.pop()
                    value1 = stack.pop()
                    res = value1 * value2
                    stack.append(res)
                elif opcode == 164:  # modulo
                    value2 = stack.pop()
                    value1 = stack.pop()
                    res = value1 % value2
                    stack.append(res)
                elif opcode == 168:  # bitand
                    value2 = stack.pop()
                    value1 = stack.pop()
                    assert isinstance(value1, int)
                    assert isinstance(value2, int)
                    res = value1 & value2
                    stack.append(res)
                elif opcode == 171:  # equals
                    value2 = stack.pop()
                    value1 = stack.pop()
                    result = value1 == value2
                    stack.append(result)
                elif opcode == 175:  # greaterequals
                    value2 = stack.pop()
                    value1 = stack.pop()
                    result = value1 >= value2
                    stack.append(result)
                elif opcode == 192:  # increment_i
                    value = stack.pop()
                    assert isinstance(value, int)
                    stack.append(value + 1)
                elif opcode == 208:  # getlocal_0
                    stack.append(registers[0])
                elif opcode == 209:  # getlocal_1
                    stack.append(registers[1])
                elif opcode == 210:  # getlocal_2
                    stack.append(registers[2])
                elif opcode == 211:  # getlocal_3
                    stack.append(registers[3])
                elif opcode == 212:  # setlocal_0
                    registers[0] = stack.pop()
                elif opcode == 213:  # setlocal_1
                    registers[1] = stack.pop()
                elif opcode == 214:  # setlocal_2
                    registers[2] = stack.pop()
                elif opcode == 215:  # setlocal_3
                    registers[3] = stack.pop()
                else:
                    raise NotImplementedError(
                        'Unsupported opcode %d' % opcode)