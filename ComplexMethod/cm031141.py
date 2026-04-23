def _parse_pattern(cls, pattern):
        """Parse a glob pattern to a list of parts. This is much like
        _parse_path, except:

        - Rather than normalizing and returning the drive and root, we raise
          NotImplementedError if either are present.
        - If the path has no real parts, we raise ValueError.
        - If the path ends in a slash, then a final empty part is added.
        """
        drv, root, rel = cls.parser.splitroot(pattern)
        if root or drv:
            raise NotImplementedError("Non-relative patterns are unsupported")
        sep = cls.parser.sep
        altsep = cls.parser.altsep
        if altsep:
            rel = rel.replace(altsep, sep)
        parts = [x for x in rel.split(sep) if x and x != '.']
        if not parts:
            raise ValueError(f"Unacceptable pattern: {str(pattern)!r}")
        elif rel.endswith(sep):
            # GH-65238: preserve trailing slash in glob patterns.
            parts.append('')
        return parts