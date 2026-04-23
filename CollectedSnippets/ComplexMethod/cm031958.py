def process_args(args, *, argv=None):
        ns = vars(args)

        kinds = []
        for kind in ns.pop('kinds') or default or ():
            kinds.extend(kind.strip().replace(',', ' ').split())

        if not kinds:
            match_kind = (lambda k: True)
        else:
            included = set()
            excluded = set()
            for kind in kinds:
                if kind.startswith('-'):
                    kind = kind[1:]
                    excluded.add(kind)
                    if kind in included:
                        included.remove(kind)
                else:
                    included.add(kind)
                    if kind in excluded:
                        excluded.remove(kind)
            if excluded:
                if included:
                    ...  # XXX fail?
                def match_kind(kind, *, _excluded=excluded):
                    return kind not in _excluded
            else:
                def match_kind(kind, *, _included=included):
                    return kind in _included
        args.match_kind = match_kind