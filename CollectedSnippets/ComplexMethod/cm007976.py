def interpret_statement(self, stmt, local_vars, allow_recursion=100, _is_var_declaration=False):
        if allow_recursion < 0:
            raise self.Exception('Recursion limit reached')
        allow_recursion -= 1

        should_return = False
        sub_statements = list(self._separate(stmt, ';')) or ['']
        expr = stmt = sub_statements.pop().strip()

        for sub_stmt in sub_statements:
            ret, should_return = self.interpret_statement(sub_stmt, local_vars, allow_recursion)
            if should_return:
                return ret, should_return

        m = re.match(r'(?P<var>(?:var|const|let)\s)|return(?:\s+|(?=["\'])|$)|(?P<throw>throw\s+)', stmt)
        if m:
            expr = stmt[len(m.group(0)):].strip()
            if m.group('throw'):
                raise JS_Throw(self.interpret_expression(expr, local_vars, allow_recursion))
            should_return = not m.group('var')
            _is_var_declaration = _is_var_declaration or bool(m.group('var'))
        if not expr:
            return None, should_return

        if expr[0] in _QUOTES:
            inner, outer = self._separate(expr, expr[0], 1)
            if expr[0] == '/':
                flags, outer = self._regex_flags(outer)
                # We don't support regex methods yet, so no point compiling it
                inner = f'{inner}/{flags}'
                # Avoid https://github.com/python/cpython/issues/74534
                # inner = re.compile(inner[1:].replace('[[', r'[\['), flags=flags)
            else:
                inner = json.loads(js_to_json(f'{inner}{expr[0]}', strict=True))
            if not outer:
                return inner, should_return
            expr = self._named_object(local_vars, inner) + outer

        if expr.startswith('new '):
            obj = expr[4:]
            if obj.startswith('Date('):
                left, right = self._separate_at_paren(obj[4:])
                date = unified_timestamp(
                    self.interpret_expression(left, local_vars, allow_recursion), False)
                if date is None:
                    raise self.Exception(f'Failed to parse date {left!r}', expr)
                expr = self._dump(int(date * 1000), local_vars) + right
            else:
                raise self.Exception(f'Unsupported object {obj}', expr)

        if expr.startswith('void '):
            left = self.interpret_expression(expr[5:], local_vars, allow_recursion)
            return None, should_return

        if expr.startswith('{'):
            inner, outer = self._separate_at_paren(expr)
            # try for object expression (Map)
            sub_expressions = [list(self._separate(sub_expr.strip(), ':', 1)) for sub_expr in self._separate(inner)]
            if all(len(sub_expr) == 2 for sub_expr in sub_expressions):
                def dict_item(key, val):
                    val = self.interpret_expression(val, local_vars, allow_recursion)
                    if re.match(_NAME_RE, key):
                        return key, val
                    return self.interpret_expression(key, local_vars, allow_recursion), val

                return dict(dict_item(k, v) for k, v in sub_expressions), should_return

            inner, should_abort = self.interpret_statement(inner, local_vars, allow_recursion)
            if not outer or should_abort:
                return inner, should_abort or should_return
            else:
                expr = self._dump(inner, local_vars) + outer

        if expr.startswith('('):
            inner, outer = self._separate_at_paren(expr)
            inner, should_abort = self.interpret_statement(inner, local_vars, allow_recursion)
            if not outer or should_abort:
                return inner, should_abort or should_return
            else:
                expr = self._dump(inner, local_vars) + outer

        if expr.startswith('['):
            inner, outer = self._separate_at_paren(expr)
            name = self._named_object(local_vars, [
                self.interpret_expression(item, local_vars, allow_recursion)
                for item in self._separate(inner)])
            expr = name + outer

        m = re.match(r'''(?x)
                (?P<try>try)\s*\{|
                (?P<if>if)\s*\(|
                (?P<switch>switch)\s*\(|
                (?P<for>for)\s*\(
                ''', expr)
        md = m.groupdict() if m else {}
        if md.get('if'):
            cndn, expr = self._separate_at_paren(expr[m.end() - 1:])
            if_expr, expr = self._separate_at_paren(expr.lstrip())
            # TODO: "else if" is not handled
            else_expr = None
            m = re.match(r'else\s*{', expr)
            if m:
                else_expr, expr = self._separate_at_paren(expr[m.end() - 1:])
            cndn = _js_ternary(self.interpret_expression(cndn, local_vars, allow_recursion))
            ret, should_abort = self.interpret_statement(
                if_expr if cndn else else_expr, local_vars, allow_recursion)
            if should_abort:
                return ret, True

        if md.get('try'):
            try_expr, expr = self._separate_at_paren(expr[m.end() - 1:])
            err = None
            try:
                ret, should_abort = self.interpret_statement(try_expr, local_vars, allow_recursion)
                if should_abort:
                    return ret, True
            except Exception as e:
                # XXX: This works for now, but makes debugging future issues very hard
                err = e

            pending = (None, False)
            m = re.match(fr'catch\s*(?P<err>\(\s*{_NAME_RE}\s*\))?\{{', expr)
            if m:
                sub_expr, expr = self._separate_at_paren(expr[m.end() - 1:])
                if err:
                    catch_vars = {}
                    if m.group('err'):
                        catch_vars[m.group('err')] = err.error if isinstance(err, JS_Throw) else err
                    catch_vars = local_vars.new_child(catch_vars)
                    err, pending = None, self.interpret_statement(sub_expr, catch_vars, allow_recursion)

            m = re.match(r'finally\s*\{', expr)
            if m:
                sub_expr, expr = self._separate_at_paren(expr[m.end() - 1:])
                ret, should_abort = self.interpret_statement(sub_expr, local_vars, allow_recursion)
                if should_abort:
                    return ret, True

            ret, should_abort = pending
            if should_abort:
                return ret, True

            if err:
                raise err

        elif md.get('for'):
            constructor, remaining = self._separate_at_paren(expr[m.end() - 1:])
            if remaining.startswith('{'):
                body, expr = self._separate_at_paren(remaining)
            else:
                switch_m = re.match(r'switch\s*\(', remaining)  # FIXME: ?
                if switch_m:
                    switch_val, remaining = self._separate_at_paren(remaining[switch_m.end() - 1:])
                    body, expr = self._separate_at_paren(remaining, '}')
                    body = 'switch(%s){%s}' % (switch_val, body)
                else:
                    body, expr = remaining, ''
            start, cndn, increment = self._separate(constructor, ';')
            self.interpret_expression(start, local_vars, allow_recursion)
            while True:
                if not _js_ternary(self.interpret_expression(cndn, local_vars, allow_recursion)):
                    break
                try:
                    ret, should_abort = self.interpret_statement(body, local_vars, allow_recursion)
                    if should_abort:
                        return ret, True
                except JS_Break:
                    break
                except JS_Continue:
                    pass
                self.interpret_expression(increment, local_vars, allow_recursion)

        elif md.get('switch'):
            switch_val, remaining = self._separate_at_paren(expr[m.end() - 1:])
            switch_val = self.interpret_expression(switch_val, local_vars, allow_recursion)
            body, expr = self._separate_at_paren(remaining, '}')
            items = body.replace('default:', 'case default:').split('case ')[1:]
            for default in (False, True):
                matched = False
                for item in items:
                    case, stmt = (i.strip() for i in self._separate(item, ':', 1))
                    if default:
                        matched = matched or case == 'default'
                    elif not matched:
                        matched = (case != 'default'
                                   and switch_val == self.interpret_expression(case, local_vars, allow_recursion))
                    if not matched:
                        continue
                    try:
                        ret, should_abort = self.interpret_statement(stmt, local_vars, allow_recursion)
                        if should_abort:
                            return ret
                    except JS_Break:
                        break
                if matched:
                    break

        if md:
            ret, should_abort = self.interpret_statement(expr, local_vars, allow_recursion)
            return ret, should_abort or should_return

        # Comma separated statements
        sub_expressions = list(self._separate(expr))
        if len(sub_expressions) > 1:
            for sub_expr in sub_expressions:
                ret, should_abort = self.interpret_statement(
                    sub_expr, local_vars, allow_recursion, _is_var_declaration=_is_var_declaration)
                if should_abort:
                    return ret, True
            return ret, False

        m = re.match(fr'''(?x)
                (?P<out>{_NAME_RE})(?:\[(?P<index>{_NESTED_BRACKETS})\])?\s*
                (?P<op>{"|".join(map(re.escape, set(_OPERATORS) - _COMP_OPERATORS))})?
                =(?!=)(?P<expr>.*)$
            ''', expr)
        if m:  # We are assigning a value to a variable
            left_val = local_vars.get(m.group('out'))

            if not m.group('index'):
                eval_result = self._operator(
                    m.group('op'), left_val, m.group('expr'), expr, local_vars, allow_recursion)
                if _is_var_declaration:
                    local_vars.set_local(m.group('out'), eval_result)
                else:
                    local_vars[m.group('out')] = eval_result
                return local_vars[m.group('out')], should_return
            elif left_val in (None, JS_Undefined):
                raise self.Exception(f'Cannot index undefined variable {m.group("out")}', expr)

            idx = self.interpret_expression(m.group('index'), local_vars, allow_recursion)
            if not isinstance(idx, (int, float)):
                raise self.Exception(f'List index {idx} must be integer', expr)
            idx = int(idx)
            left_val[idx] = self._operator(
                m.group('op'), self._index(left_val, idx), m.group('expr'), expr, local_vars, allow_recursion)
            return left_val[idx], should_return

        for m in re.finditer(rf'''(?x)
                (?P<pre_sign>\+\+|--)(?P<var1>{_NAME_RE})|
                (?P<var2>{_NAME_RE})(?P<post_sign>\+\+|--)''', expr):
            var = m.group('var1') or m.group('var2')
            start, end = m.span()
            sign = m.group('pre_sign') or m.group('post_sign')
            ret = local_vars[var]
            local_vars[var] += 1 if sign[0] == '+' else -1
            if m.group('pre_sign'):
                ret = local_vars[var]
            expr = expr[:start] + self._dump(ret, local_vars) + expr[end:]

        if not expr:
            return None, should_return

        m = re.match(fr'''(?x)
            (?P<return>
                (?!if|return|true|false|null|undefined|NaN)(?P<name>{_NAME_RE})$
            )|(?P<attribute>
                (?P<var>{_NAME_RE})(?:
                    (?P<nullish>\?)?\.(?P<member>[^(]+)|
                    \[(?P<member2>{_NESTED_BRACKETS})\]
                )\s*
            )|(?P<indexing>
                (?P<in>{_NAME_RE})\[(?P<idx>.+)\]$
            )|(?P<function>
                (?P<fname>{_NAME_RE})\((?P<args>.*)\)$
            )''', expr)
        if expr.isdigit():
            return int(expr), should_return

        elif expr == 'break':
            raise JS_Break
        elif expr == 'continue':
            raise JS_Continue
        elif expr == 'undefined':
            return JS_Undefined, should_return
        elif expr == 'NaN':
            return float('NaN'), should_return

        elif m and m.group('return'):
            var = m.group('name')
            # Declared variables
            if _is_var_declaration:
                ret = local_vars.get_local(var)
                # Register varname in local namespace
                # Set value as JS_Undefined or its pre-existing value
                local_vars.set_local(var, ret)
            else:
                ret = local_vars.get(var, NO_DEFAULT)
                if ret is NO_DEFAULT:
                    ret = JS_Undefined
                    self._undefined_varnames.add(var)
            return ret, should_return

        with contextlib.suppress(ValueError):
            return json.loads(js_to_json(expr, strict=True)), should_return

        if m and m.group('indexing'):
            val = local_vars[m.group('in')]
            idx = self.interpret_expression(m.group('idx'), local_vars, allow_recursion)
            return self._index(val, idx), should_return

        for op in _OPERATORS:
            separated = list(self._separate(expr, op))
            right_expr = separated.pop()
            while True:
                if op in '?<>*-' and len(separated) > 1 and not separated[-1].strip():
                    separated.pop()
                elif not (separated and op == '?' and right_expr.startswith('.')):
                    break
                right_expr = f'{op}{right_expr}'
                if op != '-':
                    right_expr = f'{separated.pop()}{op}{right_expr}'
            if not separated:
                continue
            left_val = self.interpret_expression(op.join(separated), local_vars, allow_recursion)
            return self._operator(op, left_val, right_expr, expr, local_vars, allow_recursion), should_return

        if m and m.group('attribute'):
            variable, member, nullish = m.group('var', 'member', 'nullish')
            if not member:
                member = self.interpret_expression(m.group('member2'), local_vars, allow_recursion)
            arg_str = expr[m.end():]
            if arg_str.startswith('('):
                arg_str, remaining = self._separate_at_paren(arg_str)
            else:
                arg_str, remaining = None, arg_str

            def assertion(cndn, msg):
                """ assert, but without risk of getting optimized out """
                if not cndn:
                    raise self.Exception(f'{member} {msg}', expr)

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

            if remaining:
                ret, should_abort = self.interpret_statement(
                    self._named_object(local_vars, eval_method()) + remaining,
                    local_vars, allow_recursion)
                return ret, should_return or should_abort
            else:
                return eval_method(), should_return

        elif m and m.group('function'):
            fname = m.group('fname')
            argvals = [self.interpret_expression(v, local_vars, allow_recursion)
                       for v in self._separate(m.group('args'))]
            if fname in local_vars:
                return local_vars[fname](argvals, allow_recursion=allow_recursion), should_return
            elif fname not in self._functions:
                self._functions[fname] = self.extract_function(fname)
            return self._functions[fname](argvals, allow_recursion=allow_recursion), should_return

        raise self.Exception(
            f'Unsupported JS expression {truncate_string(expr, 20, 20) if expr != stmt else ""}', stmt)