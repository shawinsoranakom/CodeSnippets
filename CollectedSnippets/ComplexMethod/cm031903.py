def parse_function_body(name, text, resolve, source, anon_name, parent):
    raise NotImplementedError
    # For now we do not worry about locals declared in for loop "headers".
    depth = 1;
    while depth > 0:
        m = LOCAL_RE.match(text)
        while not m:
            text, resolve = continue_text(source, text or '{', resolve)
            m = LOCAL_RE.match(text)
        text = text[m.end():]
        (
         empty,
         inline_leading, inline_pre, inline_kind, inline_name,
         storage, decl,
         var_init, var_ending,
         compound_bare, compound_labeled, compound_paren,
         block_leading, block_open,
         simple_stmt, simple_ending,
         block_close,
         ) = m.groups()

        if empty:
            log_match('', m, depth)
            resolve(None, None, None, text)
            yield None, text
        elif inline_kind:
            log_match('', m, depth)
            kind = inline_kind
            name = inline_name or anon_name('inline-')
            data = []  # members
            # We must set the internal "text" from _iter_source() to the
            # start of the inline compound body,
            # Note that this is effectively like a forward reference that
            # we do not emit.
            resolve(kind, None, name, text, None)
            _parse_body = DECL_BODY_PARSERS[kind]
            before = []
            ident = f'{kind} {name}'
            for member, inline, text in _parse_body(text, resolve, source, anon_name, ident):
                if member:
                    data.append(member)
                if inline:
                    yield from inline
            # un-inline the decl.  Note that it might not actually be inline.
            # We handle the case in the "maybe_inline_actual" branch.
            text = f'{inline_leading or ""} {inline_pre or ""} {kind} {name} {text}'
            # XXX Should "parent" really be None for inline type decls?
            yield resolve(kind, data, name, text, None), text
        elif block_close:
            log_match('', m, depth)
            depth -= 1
            resolve(None, None, None, text)
            # XXX This isn't great.  Calling resolve() should have
            # cleared the closing bracket.  However, some code relies
            # on the yielded value instead of the resolved one.  That
            # needs to be fixed.
            yield None, text
        elif compound_bare:
            log_match('', m, depth)
            yield resolve('statement', compound_bare, None, text, parent), text
        elif compound_labeled:
            log_match('', m, depth)
            yield resolve('statement', compound_labeled, None, text, parent), text
        elif compound_paren:
            log_match('', m, depth)
            try:
                pos = match_paren(text)
            except ValueError:
                text = f'{compound_paren} {text}'
                #resolve(None, None, None, text)
                text, resolve = continue_text(source, text, resolve)
                yield None, text
            else:
                head = text[:pos]
                text = text[pos:]
                if compound_paren == 'for':
                    # XXX Parse "head" as a compound statement.
                    stmt1, stmt2, stmt3 = head.split(';', 2)
                    data = {
                        'compound': compound_paren,
                        'statements': (stmt1, stmt2, stmt3),
                    }
                else:
                    data = {
                        'compound': compound_paren,
                        'statement': head,
                    }
                yield resolve('statement', data, None, text, parent), text
        elif block_open:
            log_match('', m, depth)
            depth += 1
            if block_leading:
                # An inline block: the last evaluated expression is used
                # in place of the block.
                # XXX Combine it with the remainder after the block close.
                stmt = f'{block_open}{{<expr>}}...;'
                yield resolve('statement', stmt, None, text, parent), text
            else:
                resolve(None, None, None, text)
                yield None, text
        elif simple_ending:
            log_match('', m, depth)
            yield resolve('statement', simple_stmt, None, text, parent), text
        elif var_ending:
            log_match('', m, depth)
            kind = 'variable'
            _, name, vartype = parse_var_decl(decl)
            data = {
                'storage': storage,
                'vartype': vartype,
            }
            after = ()
            if var_ending == ',':
                # It was a multi-declaration, so queue up the next one.
                _, qual, typespec, _ = vartype.values()
                text = f'{storage or ""} {qual or ""} {typespec} {text}'
            yield resolve(kind, data, name, text, parent), text
            if var_init:
                _data = f'{name} = {var_init.strip()}'
                yield resolve('statement', _data, None, text, parent), text
        else:
            # This should be unreachable.
            raise NotImplementedError