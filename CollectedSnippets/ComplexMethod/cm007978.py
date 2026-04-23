def eval_method():
                nonlocal member

                if (variable, member) == ('console', 'debug'):
                    if Debugger.ENABLED:
                        Debugger.write(self.interpret_expression(f'[{arg_str}]', local_vars, allow_recursion))
                    return

                types = {
                    'String': str,
                    'Math': float,
                    'Array': list,
                }
                obj = local_vars.get(variable, types.get(variable, NO_DEFAULT))
                if obj is NO_DEFAULT:
                    if variable not in self._objects:
                        try:
                            self._objects[variable] = self.extract_object(variable, local_vars)
                        except self.Exception:
                            if not nullish:
                                raise
                    obj = self._objects.get(variable, JS_Undefined)

                if nullish and obj is JS_Undefined:
                    return JS_Undefined

                # Member access
                if arg_str is None:
                    return self._index(obj, member, nullish)

                # Function call
                argvals = [
                    self.interpret_expression(v, local_vars, allow_recursion)
                    for v in self._separate(arg_str)]

                # Fixup prototype call
                if isinstance(obj, type) and member.startswith('prototype.'):
                    new_member, _, func_prototype = member.partition('.')[2].partition('.')
                    assertion(argvals, 'takes one or more arguments')
                    assertion(isinstance(argvals[0], obj), f'needs binding to type {obj}')
                    if func_prototype == 'call':
                        obj, *argvals = argvals
                    elif func_prototype == 'apply':
                        assertion(len(argvals) == 2, 'takes two arguments')
                        obj, argvals = argvals
                        assertion(isinstance(argvals, list), 'second argument needs to be a list')
                    else:
                        raise self.Exception(f'Unsupported Function method {func_prototype}', expr)
                    member = new_member

                if obj is str:
                    if member == 'fromCharCode':
                        assertion(argvals, 'takes one or more arguments')
                        return ''.join(map(chr, argvals))
                    raise self.Exception(f'Unsupported String method {member}', expr)
                elif obj is float:
                    if member == 'pow':
                        assertion(len(argvals) == 2, 'takes two arguments')
                        return argvals[0] ** argvals[1]
                    raise self.Exception(f'Unsupported Math method {member}', expr)

                if member == 'split':
                    assertion(argvals, 'takes one or more arguments')
                    assertion(len(argvals) == 1, 'with limit argument is not implemented')
                    return obj.split(argvals[0]) if argvals[0] else list(obj)
                elif member == 'join':
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    assertion(len(argvals) == 1, 'takes exactly one argument')
                    return argvals[0].join(obj)
                elif member == 'reverse':
                    assertion(not argvals, 'does not take any arguments')
                    obj.reverse()
                    return obj
                elif member == 'slice':
                    assertion(isinstance(obj, (list, str)), 'must be applied on a list or string')
                    assertion(len(argvals) <= 2, 'takes between 0 and 2 arguments')
                    return obj[slice(*argvals, None)]
                elif member == 'splice':
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    assertion(argvals, 'takes one or more arguments')
                    index, how_many = map(int, ([*argvals, len(obj)])[:2])
                    if index < 0:
                        index += len(obj)
                    add_items = argvals[2:]
                    res = []
                    for _ in range(index, min(index + how_many, len(obj))):
                        res.append(obj.pop(index))
                    for i, item in enumerate(add_items):
                        obj.insert(index + i, item)
                    return res
                elif member == 'unshift':
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    assertion(argvals, 'takes one or more arguments')
                    for item in reversed(argvals):
                        obj.insert(0, item)
                    return obj
                elif member == 'pop':
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    assertion(not argvals, 'does not take any arguments')
                    if not obj:
                        return
                    return obj.pop()
                elif member == 'push':
                    assertion(argvals, 'takes one or more arguments')
                    obj.extend(argvals)
                    return obj
                elif member == 'forEach':
                    assertion(argvals, 'takes one or more arguments')
                    assertion(len(argvals) <= 2, 'takes at-most 2 arguments')
                    f, this = ([*argvals, ''])[:2]
                    return [f((item, idx, obj), {'this': this}, allow_recursion) for idx, item in enumerate(obj)]
                elif member == 'indexOf':
                    assertion(argvals, 'takes one or more arguments')
                    assertion(len(argvals) <= 2, 'takes at-most 2 arguments')
                    idx, start = ([*argvals, 0])[:2]
                    try:
                        return obj.index(idx, start)
                    except ValueError:
                        return -1
                elif member == 'charCodeAt':
                    assertion(isinstance(obj, str), 'must be applied on a string')
                    assertion(len(argvals) == 1, 'takes exactly one argument')
                    idx = argvals[0] if isinstance(argvals[0], int) else 0
                    if idx >= len(obj):
                        return None
                    return ord(obj[idx])

                idx = int(member) if isinstance(obj, list) else member
                return obj[idx](argvals, allow_recursion=allow_recursion)