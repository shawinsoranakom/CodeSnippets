def ewkb_w(dim=2):
    if not thread_context.ewkb_w:
        thread_context.ewkb_w = WKBWriter(dim=dim)
        thread_context.ewkb_w.srid = True
    else:
        thread_context.ewkb_w.outdim = dim
    return thread_context.ewkb_w