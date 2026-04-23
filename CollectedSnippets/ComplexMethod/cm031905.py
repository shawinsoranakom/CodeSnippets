def _parse_next_local_static(m, srcinfo, anon_name, func, depth):
    (inline_leading, inline_pre, inline_kind, inline_name,
     static_decl, static_init, static_ending,
     _delim_leading,
     block_open,
     block_close,
     stmt_end,
     ) = m.groups()
    remainder = srcinfo.text[m.end():]

    if inline_kind:
        log_match('func inline', m, depth, depth)
        kind = inline_kind
        name = inline_name or anon_name('inline-')
        # Immediately emit a forward declaration.
        yield srcinfo.resolve(kind, name=name, data=None), depth

        # un-inline the decl.  Note that it might not actually be inline.
        # We handle the case in the "maybe_inline_actual" branch.
        srcinfo.nest(
            remainder,
            f'{inline_leading or ""} {inline_pre or ""} {kind} {name}'
        )
        def parse_body(source):
            _parse_body = DECL_BODY_PARSERS[kind]

            data = []  # members
            ident = f'{kind} {name}'
            for item in _parse_body(source, anon_name, ident):
                if item.kind == 'field':
                    data.append(item)
                else:
                    yield item
            # XXX Should "parent" really be None for inline type decls?
            yield srcinfo.resolve(kind, data, name, parent=None)

            srcinfo.resume()
        yield parse_body, depth

    elif static_decl:
        log_match('local variable', m, depth, depth)
        _, name, data = parse_var_decl(static_decl)

        yield srcinfo.resolve('variable', data, name, parent=func), depth

        if static_init:
            srcinfo.advance(f'{name} {static_init} {remainder}')
        elif static_ending == ',':
            # It was a multi-declaration, so queue up the next one.
            _, qual, typespec, _ = data.values()
            srcinfo.advance(f'static {qual or ""} {typespec} {remainder}')
        else:
            srcinfo.advance('')

    else:
        log_match('func other', m)
        if block_open:
            log_match('func other', None, depth, depth + 1)
            depth += 1
        elif block_close:
            log_match('func other', None, depth, depth - 1)
            depth -= 1
        elif stmt_end:
            log_match('func other', None, depth, depth)
            pass
        else:
            # This should be unreachable.
            raise NotImplementedError
        srcinfo.advance(remainder)
        yield None, depth