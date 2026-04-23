def eval_method(variable, member):
                if (variable, member) == ('console', 'debug'):
                    if Debugger.ENABLED:
                        Debugger.write(self.interpret_expression('[{0}]'.format(arg_str), local_vars, allow_recursion))
                    return
                types = {
                    'String': compat_str,
                    'Math': float,
                    'Array': list,
                    'Date': self.JS_Date,
                    'RegExp': self.JS_RegExp,
                    # 'Error': self.Exception,  # has no std static methods
                }
                obj = local_vars.get(variable)
                if obj in (JS_Undefined, None):
                    obj = types.get(variable, JS_Undefined)
                if obj is JS_Undefined:
                    try:
                        if variable not in self._objects:
                            self._objects[variable] = self.extract_object(variable, local_vars)
                        obj = self._objects[variable]
                    except self.Exception:
                        if not nullish:
                            raise

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
                if isinstance(obj, type):
                    new_member, rest = member.partition('.')[0::2]
                    if new_member == 'prototype':
                        new_member, func_prototype = rest.partition('.')[0::2]
                        assertion(argvals, 'takes one or more arguments')
                        assertion(isinstance(argvals[0], obj), 'must bind to type {0}'.format(obj))
                        if func_prototype == 'call':
                            obj = argvals.pop(0)
                        elif func_prototype == 'apply':
                            assertion(len(argvals) == 2, 'takes two arguments')
                            obj, argvals = argvals
                            assertion(isinstance(argvals, list), 'second argument must be a list')
                        else:
                            raise self.Exception('Unsupported Function method ' + func_prototype, expr)
                        member = new_member

                if obj is compat_str:
                    if member == 'fromCharCode':
                        assertion(argvals, 'takes one or more arguments')
                        return ''.join(compat_chr(int(n)) for n in argvals)
                    raise self.Exception('Unsupported string method ' + member, expr=expr)
                elif obj is float:
                    if member == 'pow':
                        assertion(len(argvals) == 2, 'takes two arguments')
                        return argvals[0] ** argvals[1]
                    raise self.Exception('Unsupported Math method ' + member, expr=expr)
                elif obj is self.JS_Date:
                    return getattr(obj, member)(*argvals)

                if member == 'split':
                    assertion(len(argvals) <= 2, 'takes at most two arguments')
                    if len(argvals) > 1:
                        limit = argvals[1]
                        assertion(isinstance(limit, int) and limit >= 0, 'integer limit >= 0')
                        if limit == 0:
                            return []
                    else:
                        limit = 0
                    if len(argvals) == 0:
                        argvals = [JS_Undefined]
                    elif isinstance(argvals[0], self.JS_RegExp):
                        # avoid re.split(), similar but not enough

                        def where():
                            for m in argvals[0].finditer(obj):
                                yield m.span(0)
                            yield (None, None)

                        def splits(limit=limit):
                            i = 0
                            for j, jj in where():
                                if j == jj == 0:
                                    continue
                                if j is None and i >= len(obj):
                                    break
                                yield obj[i:j]
                                if jj is None or limit == 1:
                                    break
                                limit -= 1
                                i = jj

                        return list(splits())
                    return (
                        obj.split(argvals[0], limit - 1) if argvals[0] and argvals[0] != JS_Undefined
                        else list(obj)[:limit or None])
                elif member == 'join':
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    assertion(len(argvals) <= 1, 'takes at most one argument')
                    return (',' if len(argvals) == 0 or argvals[0] in (None, JS_Undefined)
                            else argvals[0]).join(
                                ('' if x in (None, JS_Undefined) else _js_toString(x))
                                for x in obj)
                elif member == 'reverse':
                    assertion(not argvals, 'does not take any arguments')
                    obj.reverse()
                    return obj
                elif member == 'slice':
                    assertion(isinstance(obj, (list, compat_str)), 'must be applied on a list or string')
                    # From [1]:
                    # .slice() - like [:]
                    # .slice(n) - like [n:] (not [slice(n)]
                    # .slice(m, n) - like [m:n] or [slice(m, n)]
                    # [1] https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/slice
                    assertion(len(argvals) <= 2, 'takes between 0 and 2 arguments')
                    if len(argvals) < 2:
                        argvals += (None,)
                    return obj[slice(*argvals)]
                elif member == 'splice':
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    assertion(argvals, 'takes one or more arguments')
                    index, how_many = map(int, (argvals + [len(obj)])[:2])
                    if index < 0:
                        index += len(obj)
                    res = [obj.pop(index)
                           for _ in range(index, min(index + how_many, len(obj)))]
                    obj[index:index] = argvals[2:]
                    return res
                elif member in ('shift', 'pop'):
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    assertion(not argvals, 'does not take any arguments')
                    return obj.pop(0 if member == 'shift' else -1) if len(obj) > 0 else JS_Undefined
                elif member == 'unshift':
                    assertion(isinstance(obj, list), 'must be applied on a list')
                    # not enforced: assertion(argvals, 'takes one or more arguments')
                    obj[0:0] = argvals
                    return len(obj)
                elif member == 'push':
                    # not enforced: assertion(argvals, 'takes one or more arguments')
                    obj.extend(argvals)
                    return len(obj)
                elif member == 'forEach':
                    assertion(argvals, 'takes one or more arguments')
                    assertion(len(argvals) <= 2, 'takes at most 2 arguments')
                    f, this = (argvals + [''])[:2]
                    return [f((item, idx, obj), {'this': this}, allow_recursion) for idx, item in enumerate(obj)]
                elif member == 'indexOf':
                    assertion(argvals, 'takes one or more arguments')
                    assertion(len(argvals) <= 2, 'takes at most 2 arguments')
                    idx, start = (argvals + [0])[:2]
                    try:
                        return obj.index(idx, start)
                    except ValueError:
                        return -1
                elif member == 'charCodeAt':
                    assertion(isinstance(obj, compat_str), 'must be applied on a string')
                    # assertion(len(argvals) == 1, 'takes exactly one argument') # but not enforced
                    idx = argvals[0] if len(argvals) > 0 and isinstance(argvals[0], int) else 0
                    if idx >= len(obj):
                        return None
                    return ord(obj[idx])
                elif member in ('replace', 'replaceAll'):
                    assertion(isinstance(obj, compat_str), 'must be applied on a string')
                    assertion(len(argvals) == 2, 'takes exactly two arguments')
                    # TODO: argvals[1] callable, other Py vs JS edge cases
                    if isinstance(argvals[0], self.JS_RegExp):
                        # access JS member with Py reserved name
                        count = 0 if self._index(argvals[0], 'global') else 1
                        assertion(member != 'replaceAll' or count == 0,
                                  'replaceAll must be called with a global RegExp')
                        return argvals[0].sub(argvals[1], obj, count=count)
                    count = ('replaceAll', 'replace').index(member)
                    return re.sub(re.escape(argvals[0]), argvals[1], obj, count=count)

                idx = int(member) if isinstance(obj, list) else member
                return obj[idx](argvals, allow_recursion=allow_recursion)