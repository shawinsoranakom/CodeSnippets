def wkb_r():
    thread_context.wkb_r = thread_context.wkb_r or _WKBReader()
    return thread_context.wkb_r