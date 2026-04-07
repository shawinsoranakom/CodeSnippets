def wkb_w(dim=2):
    if not thread_context.wkb_w:
        thread_context.wkb_w = WKBWriter(dim=dim)
    else:
        thread_context.wkb_w.outdim = dim
    return thread_context.wkb_w