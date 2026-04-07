def __repr__(self):
        if isinstance(self.func, functools.partial):
            func = repr(self.func)
        else:
            func = self._func_path
        return (
            "ResolverMatch(func=%s, args=%r, kwargs=%r, url_name=%r, "
            "app_names=%r, namespaces=%r, route=%r%s%s)"
            % (
                func,
                self.args,
                self.kwargs,
                self.url_name,
                self.app_names,
                self.namespaces,
                self.route,
                (
                    f", captured_kwargs={self.captured_kwargs!r}"
                    if self.captured_kwargs
                    else ""
                ),
                f", extra_kwargs={self.extra_kwargs!r}" if self.extra_kwargs else "",
            )
        )