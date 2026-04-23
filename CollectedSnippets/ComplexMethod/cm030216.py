def _extract_from_extended_frame_gen(klass, frame_gen, *, limit=None,
            lookup_lines=True, capture_locals=False):
        # Same as extract but operates on a frame generator that yields
        # (frame, (lineno, end_lineno, colno, end_colno)) in the stack.
        # Only lineno is required, the remaining fields can be None if the
        # information is not available.
        builtin_limit = limit is BUILTIN_EXCEPTION_LIMIT
        if limit is None or builtin_limit:
            limit = getattr(sys, 'tracebacklimit', None)
            if limit is not None and limit < 0:
                limit = 0
        if limit is not None:
            if builtin_limit:
                frame_gen = tuple(frame_gen)
                frame_gen = frame_gen[len(frame_gen) - limit:]
            elif limit >= 0:
                frame_gen = itertools.islice(frame_gen, limit)
            else:
                frame_gen = collections.deque(frame_gen, maxlen=-limit)

        result = klass()
        fnames = set()
        for f, (lineno, end_lineno, colno, end_colno) in frame_gen:
            co = f.f_code
            filename = co.co_filename
            name = co.co_name
            fnames.add(filename)
            linecache.lazycache(filename, f.f_globals)
            # Must defer line lookups until we have called checkcache.
            if capture_locals:
                f_locals = f.f_locals
            else:
                f_locals = None
            result.append(
                FrameSummary(filename, lineno, name,
                    lookup_line=False, locals=f_locals,
                    end_lineno=end_lineno, colno=colno, end_colno=end_colno,
                    _code=f.f_code,
                )
            )
        for filename in fnames:
            linecache.checkcache(filename)

        # If immediate lookup was desired, trigger lookups now.
        if lookup_lines:
            for f in result:
                f.line
        return result