def check_globals(analysis):
    # yield (data, failure)
    ignored = read_ignored()
    for item in analysis:
        if item.kind != KIND.VARIABLE:
            continue
        if item.supported:
            continue
        if item.id in ignored:
            continue
        reason = item.unsupported
        if not reason:
            reason = '???'
        elif not isinstance(reason, str):
            if len(reason) == 1:
                reason, = reason
        reason = f'({reason})'
        yield item, f'not supported {reason:20}\t{item.storage or ""} {item.vartype}'