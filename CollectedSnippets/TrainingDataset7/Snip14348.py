def async_only_middleware(func):
    """Mark a middleware factory as returning an async middleware."""
    func.sync_capable = False
    func.async_capable = True
    return func