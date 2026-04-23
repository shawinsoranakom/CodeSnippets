def __init__(
        self,
        msg: str = DEPRECATED_DEFAULT,  # type: ignore[assignment]
        doc: str = DEPRECATED_DEFAULT,  # type: ignore[assignment]
        pos: Pos = DEPRECATED_DEFAULT,  # type: ignore[assignment]
        *args: Any,
    ):
        if (
            args
            or not isinstance(msg, str)
            or not isinstance(doc, str)
            or not isinstance(pos, int)
        ):
            import warnings

            warnings.warn(
                "Free-form arguments for TOMLDecodeError are deprecated. "
                "Please set 'msg' (str), 'doc' (str) and 'pos' (int) arguments only.",
                DeprecationWarning,
                stacklevel=2,
            )
            if pos is not DEPRECATED_DEFAULT:  # type: ignore[comparison-overlap]
                args = pos, *args
            if doc is not DEPRECATED_DEFAULT:  # type: ignore[comparison-overlap]
                args = doc, *args
            if msg is not DEPRECATED_DEFAULT:  # type: ignore[comparison-overlap]
                args = msg, *args
            ValueError.__init__(self, *args)
            return

        lineno = doc.count("\n", 0, pos) + 1
        if lineno == 1:
            colno = pos + 1
        else:
            colno = pos - doc.rindex("\n", 0, pos)

        if pos >= len(doc):
            coord_repr = "end of document"
        else:
            coord_repr = f"line {lineno}, column {colno}"
        errmsg = f"{msg} (at {coord_repr})"
        ValueError.__init__(self, errmsg)

        self.msg = msg
        self.doc = doc
        self.pos = pos
        self.lineno = lineno
        self.colno = colno