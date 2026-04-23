def interpret_statement(self, stmt, local_vars, allow_recursion=100):
        if allow_recursion < 0:
            raise self.Exception('Recursion limit reached')
        allow_recursion -= 1

        # print('At: ' + stmt[:60])
        should_return = False
        # fails on (eg) if (...) stmt1; else stmt2;
        sub_statements = list(self._separate(stmt, ';')) or ['']
        expr = stmt = sub_statements.pop().strip()

        for sub_stmt in sub_statements:
            ret, should_return = self.interpret_statement(sub_stmt, local_vars, allow_recursion)
            if should_return:
                return ret, should_return

        m = self._VAR_RET_THROW_RE.match(stmt)
        if m:
            expr = stmt[len(m.group(0)):].strip()
            if m.group('throw'):
                raise JS_Throw(self.interpret_expression(expr, local_vars, allow_recursion))
            should_return = 'return' if m.group('ret') else False
        if not expr:
            return None, should_return

        if expr[0] in _QUOTES:
            inner, outer = self._separate(expr, expr[0], 1)
            if expr[0] == '/':
                flags, outer = self.JS_RegExp.regex_flags(outer)
                inner = self.JS_RegExp(inner[1:], flags=flags)
            else:
                inner = json.loads(js_to_json(inner + expr[0]))  # , strict=True))
            if not outer:
                return inner, should_return
            expr = self._named_object(local_vars, inner) + outer

        new_kw, _, obj = expr.partition('new ')
        if not new_kw:
            for klass, konstr in (('Date', lambda *x: self.JS_Date(*x).valueOf()),
                                  ('RegExp', self.JS_RegExp),
                                  ('Error', self.Exception)):
                if not obj.startswith(klass + '('):
                    continue
                left, right = self._separate_at_paren(obj[len(klass):])
                argvals = self.interpret_iter(left, local_vars, allow_recursion)
                expr = konstr(*argvals)
                if expr is None:
                    raise self.Exception('Failed to parse {klass} {left!r:.100}'.format(**locals()), expr=expr)
                expr = self._dump(expr, local_vars) + right
                break
            else:
                raise self.Exception('Unsupported object {obj:.100}'.format(**locals()), expr=expr)

        # apply unary operators (see new above)
        for op, _ in _UNARY_OPERATORS_X:
            if not expr.startswith(op):
                continue
            operand = expr[len(op):]
            if not operand or (op.isalpha() and operand[0] != ' '):
                continue
            separated = self._separate_at_op(operand, max_split=1)
            if separated:
                next_op, separated, right_expr = separated
                separated.append(right_expr)
                operand = next_op.join(separated)
            return self._eval_operator(op, operand, '', expr, local_vars, allow_recursion), should_return

        if expr.startswith('{'):
            inner, outer = self._separate_at_paren(expr)
            # try for object expression (Map)
            sub_expressions = [list(self._separate(sub_expr.strip(), ':', 1)) for sub_expr in self._separate(inner)]
            if all(len(sub_expr) == 2 for sub_expr in sub_expressions):
                return dict(
                    (key_expr if re.match(_NAME_RE, key_expr) else key_expr,
                     self.interpret_expression(val_expr, local_vars, allow_recursion))
                    for key_expr, val_expr in sub_expressions), should_return
            # or statement list
            inner, should_abort = self.interpret_statement(inner, local_vars, allow_recursion)
            if not outer or should_abort:
                return inner, should_abort or should_return
            else:
                expr = self._dump(inner, local_vars) + outer

        if expr.startswith('('):
            m = re.match(r'\((?P<d>[a-z])%(?P<e>[a-z])\.length\+(?P=e)\.length\)%(?P=e)\.length', expr)
            if m:
                # short-cut eval of frequently used `(d%e.length+e.length)%e.length`, worth ~6% on `pytest -k test_nsig`
                outer = None
                inner, should_abort = self._offset_e_by_d(m.group('d'), m.group('e'), local_vars)
            else:
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

        m = self._COMPOUND_RE.match(expr)
        md = m.groupdict() if m else {}
        if md.get('if'):
            cndn, expr = self._separate_at_paren(expr[m.end() - 1:])
            if expr.startswith('{'):
                if_expr, expr = self._separate_at_paren(expr)
            else:
                # may lose ... else ... because of ll.368-374
                if_expr, expr = self._separate_at_paren(' %s;' % (expr,), delim=';')
            else_expr = None
            m = re.match(r'else\s*(?P<block>\{)?', expr)
            if m:
                if m.group('block'):
                    else_expr, expr = self._separate_at_paren(expr[m.end() - 1:])
                else:
                    # handle subset ... else if (...) {...} else ...
                    # TODO: make interpret_statement do this properly, if possible
                    exprs = list(self._separate(expr[m.end():], delim='}', max_split=2))
                    if len(exprs) > 1:
                        if re.match(r'\s*if\s*\(', exprs[0]) and re.match(r'\s*else\b', exprs[1]):
                            else_expr = exprs[0] + '}' + exprs[1]
                            expr = (exprs[2] + '}') if len(exprs) == 3 else None
                        else:
                            else_expr = exprs[0]
                            exprs.append('')
                            expr = '}'.join(exprs[1:])
                    else:
                        else_expr = exprs[0]
                        expr = None
                    else_expr = else_expr.lstrip() + '}'
            cndn = _js_ternary(self.interpret_expression(cndn, local_vars, allow_recursion))
            ret, should_abort = self.interpret_statement(
                if_expr if cndn else else_expr, local_vars, allow_recursion)
            if should_abort:
                return ret, True

        elif md.get('try'):
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
            m = re.match(r'catch\s*(?P<err>\(\s*{_NAME_RE}\s*\))?\{{'.format(**globals()), expr)
            if m:
                sub_expr, expr = self._separate_at_paren(expr[m.end() - 1:])
                if err:
                    catch_vars = {}
                    if m.group('err'):
                        catch_vars[m.group('err')] = err.error if isinstance(err, JS_Throw) else err
                    catch_vars = local_vars.new_child(m=catch_vars)
                    err, pending = None, self.interpret_statement(sub_expr, catch_vars, allow_recursion)

            m = self._FINALLY_RE.match(expr)
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

        elif md.get('for') or md.get('while'):
            init_or_cond, remaining = self._separate_at_paren(expr[m.end() - 1:])
            if remaining.startswith('{'):
                body, expr = self._separate_at_paren(remaining)
            else:
                switch_m = self._SWITCH_RE.match(remaining)  # FIXME
                if switch_m:
                    switch_val, remaining = self._separate_at_paren(remaining[switch_m.end() - 1:])
                    body, expr = self._separate_at_paren(remaining, '}')
                    body = 'switch(%s){%s}' % (switch_val, body)
                else:
                    body, expr = remaining, ''
            if md.get('for'):
                start, cndn, increment = self._separate(init_or_cond, ';')
                self.interpret_expression(start, local_vars, allow_recursion)
            else:
                cndn, increment = init_or_cond, None
            while _js_ternary(self.interpret_expression(cndn, local_vars, allow_recursion)):
                try:
                    ret, should_abort = self.interpret_statement(body, local_vars, allow_recursion)
                    if should_abort:
                        return ret, True
                except JS_Break:
                    break
                except JS_Continue:
                    pass
                if increment:
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
                ret, should_abort = self.interpret_statement(sub_expr, local_vars, allow_recursion)
                if should_abort:
                    return ret, True
            return ret, False

        for m in re.finditer(r'''(?x)
                (?P<pre_sign>\+\+|--)(?P<var1>{_NAME_RE})|
                (?P<var2>{_NAME_RE})(?P<post_sign>\+\+|--)'''.format(**globals()), expr):
            var = m.group('var1') or m.group('var2')
            start, end = m.span()
            sign = m.group('pre_sign') or m.group('post_sign')
            ret = local_vars[var]
            local_vars[var] = _js_add(ret, 1 if sign[0] == '+' else -1)
            if m.group('pre_sign'):
                ret = local_vars[var]
            expr = expr[:start] + self._dump(ret, local_vars) + expr[end:]

        if not expr:
            return None, should_return

        m = re.match(r'''(?x)
            (?P<assign>
                (?P<out>{_NAME_RE})(?P<out_idx>(?:\[{_NESTED_BRACKETS}\])+)?\s*
                (?P<op>{_OPERATOR_RE})?
                =(?!=)(?P<expr>.*)$
            )|(?P<return>
                (?!if|return|true|false|null|undefined|NaN|Infinity)(?P<name>{_NAME_RE})$
            )|(?P<attribute>
                (?P<var>{_NAME_RE})(?:
                    (?P<nullish>\?)?\.(?P<member>[^(]+)|
                    \[(?P<member2>{_NESTED_BRACKETS})\]
                )\s*
            )|(?P<indexing>
                (?P<in>{_NAME_RE})(?P<in_idx>\[.+\])$
            )|(?P<function>
                (?P<fname>{_NAME_RE})\((?P<args>.*)\)$
            )'''.format(**globals()), expr)
        md = m.groupdict() if m else {}
        if md.get('assign'):
            left_val = local_vars.get(m.group('out'))

            if not m.group('out_idx'):
                local_vars[m.group('out')] = self._operator(
                    m.group('op'), left_val, m.group('expr'), expr, local_vars, allow_recursion)
                return local_vars[m.group('out')], should_return
            elif left_val in (None, JS_Undefined):
                raise self.Exception('Cannot index undefined variable ' + m.group('out'), expr=expr)

            indexes = md['out_idx']
            while indexes:
                idx, indexes = self._separate_at_paren(indexes)
                idx = self.interpret_expression(idx, local_vars, allow_recursion)
                if indexes:
                    left_val = self._index(left_val, idx)
            if isinstance(idx, float):
                idx = int(idx)
            if isinstance(left_val, list) and len(left_val) <= int_or_none(idx, default=-1):
                # JS Array is a sparsely assignable list
                # TODO: handle extreme sparsity without memory bloat, eg using auxiliary dict
                left_val.extend((idx - len(left_val) + 1) * [JS_Undefined])
            left_val[idx] = self._operator(
                m.group('op'), self._index(left_val, idx) if m.group('op') else None,
                m.group('expr'), expr, local_vars, allow_recursion)
            return left_val[idx], should_return

        elif expr.isdigit():
            return int(expr), should_return

        elif expr == 'break':
            raise JS_Break()
        elif expr == 'continue':
            raise JS_Continue()
        elif expr == 'undefined':
            return JS_Undefined, should_return
        elif expr == 'NaN':
            return _NaN, should_return
        elif expr == 'Infinity':
            return _Infinity, should_return

        elif md.get('return'):
            ret = local_vars[m.group('name')]
            # challenge may try to force returning the original value
            # use an optional internal var to block this
            if should_return == 'return':
                if '_ytdl_do_not_return' not in local_vars:
                    return ret, True
                return (ret, True) if ret != local_vars['_ytdl_do_not_return'] else (ret, False)
            else:
                return ret, should_return

        with compat_contextlib_suppress(ValueError):
            ret = json.loads(js_to_json(expr))  # strict=True)
            if not md.get('attribute'):
                return ret, should_return

        if md.get('indexing'):
            val = local_vars[m.group('in')]
            indexes = m.group('in_idx')
            while indexes:
                idx, indexes = self._separate_at_paren(indexes)
                idx = self.interpret_expression(idx, local_vars, allow_recursion)
                val = self._index(val, idx)
            return val, should_return

        separated = self._separate_at_op(expr)
        if separated:
            op, separated, right_expr = separated
            return self._eval_operator(op, op.join(separated), right_expr, expr, local_vars, allow_recursion), should_return

        if md.get('attribute'):
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
                    memb = member
                    raise self.Exception('{memb} {msg}'.format(**locals()), expr=expr)

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

            if remaining:
                ret, should_abort = self.interpret_statement(
                    self._named_object(local_vars, eval_method(variable, member)) + remaining,
                    local_vars, allow_recursion)
                return ret, should_return or should_abort
            else:
                return eval_method(variable, member), should_return

        elif md.get('function'):
            fname = m.group('fname')
            argvals = [self.interpret_expression(v, local_vars, allow_recursion)
                       for v in self._separate(m.group('args'))]
            if fname in local_vars:
                return local_vars[fname](argvals, allow_recursion=allow_recursion), should_return
            elif fname not in self._functions:
                self._functions[fname] = self.extract_function(fname)
            return self._functions[fname](argvals, allow_recursion=allow_recursion), should_return

        raise self.Exception(
            'Unsupported JS expression ' + (expr[:40] if expr != stmt else ''), expr=stmt)