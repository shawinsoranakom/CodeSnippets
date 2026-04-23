def _parse_single_key_sequence(key: str, s: int) -> tuple[list[str], int]:
    ctrl = 0
    meta = 0
    ret = ""
    while not ret and s < len(key):
        if key[s] == "\\":
            c = key[s + 1].lower()
            if c in _escapes:
                ret = _escapes[c]
                s += 2
            elif c == "c":
                if key[s + 2] != "-":
                    raise KeySpecError(
                        "\\C must be followed by `-' (char %d of %s)"
                        % (s + 2, repr(key))
                    )
                if ctrl:
                    raise KeySpecError(
                        "doubled \\C- (char %d of %s)" % (s + 1, repr(key))
                    )
                ctrl = 1
                s += 3
            elif c == "m":
                if key[s + 2] != "-":
                    raise KeySpecError(
                        "\\M must be followed by `-' (char %d of %s)"
                        % (s + 2, repr(key))
                    )
                if meta:
                    raise KeySpecError(
                        "doubled \\M- (char %d of %s)" % (s + 1, repr(key))
                    )
                meta = 1
                s += 3
            elif c.isdigit():
                n = key[s + 1 : s + 4]
                ret = chr(int(n, 8))
                s += 4
            elif c == "x":
                n = key[s + 2 : s + 4]
                ret = chr(int(n, 16))
                s += 4
            elif c == "<":
                t = key.find(">", s)
                if t == -1:
                    raise KeySpecError(
                        "unterminated \\< starting at char %d of %s"
                        % (s + 1, repr(key))
                    )
                ret = key[s + 2 : t].lower()
                if ret not in _keynames:
                    raise KeySpecError(
                        "unrecognised keyname `%s' at char %d of %s"
                        % (ret, s + 2, repr(key))
                    )
                ret = _keynames[ret]
                s = t + 1
            else:
                raise KeySpecError(
                    "unknown backslash escape %s at char %d of %s"
                    % (repr(c), s + 2, repr(key))
                )
        else:
            ret = key[s]
            s += 1
    if ctrl:
        if len(ret) == 1:
            ret = chr(ord(ret) & 0x1F)  # curses.ascii.ctrl()
        elif ret in {"left", "right"}:
            ret = f"ctrl {ret}"
        else:
            raise KeySpecError("\\C- followed by invalid key")

    result = [ret], s
    if meta:
        result[0].insert(0, "\033")
    return result