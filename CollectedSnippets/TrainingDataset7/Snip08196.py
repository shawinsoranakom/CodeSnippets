def close_caches(**kwargs):
    # Some caches need to do a cleanup at the end of a request cycle. If not
    # implemented in a particular backend cache.close() is a no-op.
    caches.close_all()