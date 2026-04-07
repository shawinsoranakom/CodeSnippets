def wkt_w(dim=2, trim=False, precision=None):
    if not thread_context.wkt_w:
        thread_context.wkt_w = WKTWriter(dim=dim, trim=trim, precision=precision)
    else:
        thread_context.wkt_w.outdim = dim
        thread_context.wkt_w.trim = trim
        thread_context.wkt_w.precision = precision
    return thread_context.wkt_w