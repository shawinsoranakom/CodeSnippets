def filter_forward(items, *, markpublic=False):
    if markpublic:
        public = set()
        actual = []
        for item in items:
            if is_public_api(item):
                public.add(item.id)
            elif not _match.is_forward_decl(item):
                actual.append(item)
            else:
                # non-public duplicate!
                # XXX
                raise Exception(item)
        for item in actual:
            _info.set_flag(item, 'is_public', item.id in public)
            yield item
    else:
        for item in items:
            if _match.is_forward_decl(item):
                continue
            yield item