def trim_url(self, x, *, limit):
        if limit is None or len(x) <= limit:
            return x
        return "%s…" % x[: max(0, limit - 1)]