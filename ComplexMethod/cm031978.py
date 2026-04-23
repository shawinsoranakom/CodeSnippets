def _parse_raw_resolved(cls, item, resolved, extra_extra):
        if resolved in (UNKNOWN, IGNORED):
            return resolved, None
        try:
            typedeps, extra = resolved
        except (TypeError, ValueError):
            typedeps = extra = None
        if extra:
            # The resolved data takes precedence.
            extra = dict(extra_extra, **extra)
        if isinstance(typedeps, TypeDeclaration):
            return typedeps, extra
        elif typedeps in (None, UNKNOWN):
            # It is still effectively unresolved.
            return UNKNOWN, extra
        elif None in typedeps or UNKNOWN in typedeps:
            # It is still effectively unresolved.
            return typedeps, extra
        elif any(not isinstance(td, TypeDeclaration) for td in typedeps):
            raise NotImplementedError((item, typedeps, extra))
        return typedeps, extra