def wkt_r():
    thread_context.wkt_r = thread_context.wkt_r or _WKTReader()
    return thread_context.wkt_r