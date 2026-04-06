def _safe(fn, fallback):
        try:
            return fn()
        except OSError:
            return fallback