def _parse_struct_next(m, srcinfo, anon_name, parent):
    (inline_kind, inline_name,
     qualspec, declarator,
     size,
     ending,
     close,
     ) = m.groups()
    remainder = srcinfo.text[m.end():]

    if close:
        log_match('compound close', m)
        srcinfo.advance(remainder)

    elif inline_kind:
        log_match('compound inline', m)
        kind = inline_kind
        name = inline_name or anon_name('inline-')
        # Immediately emit a forward declaration.
        yield srcinfo.resolve(kind, name=name, data=None)

        # un-inline the decl.  Note that it might not actually be inline.
        # We handle the case in the "maybe_inline_actual" branch.
        srcinfo.nest(
            remainder,
            f'{kind} {name}',
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
        yield parse_body

    else:
        # not inline (member)
        log_match('compound member', m)
        if qualspec:
            _, name, data = parse_var_decl(f'{qualspec} {declarator}')
            if not name:
                name = anon_name('struct-field-')
            if size:
#                data = (data, size)
                data['size'] = int(size) if size.isdigit() else size
        else:
            # This shouldn't happen (we expect each field to have a name).
            raise NotImplementedError
            name = sized_name or anon_name('struct-field-')
            data = int(size)

        yield srcinfo.resolve('field', data, name, parent)  # XXX Restart?
        if ending == ',':
            remainder = rf'{qualspec} {remainder}'
        srcinfo.advance(remainder)