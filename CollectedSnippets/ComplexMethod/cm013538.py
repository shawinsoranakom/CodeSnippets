def _find_frame_locals(self) -> _FrameLocalResult:
        """
        Given the current user code frame, finds the relevant lines of code,
        values of symbolic locals, and free symbols involved.
        """
        frame_locals: dict[str, Any] = {}
        frame_symbols: dict[str, str] = {}

        if (
            frame := _find_user_code_frame()
        ) is None or frame.f_code.co_filename == "<string>":
            return _FrameLocalResult()

        # find bytecode instructions relevant to the frame
        instructions = list(dis.Bytecode(frame.f_code))
        co_lines, offset = inspect.getsourcelines(frame.f_code)
        start, end, cur = None, None, None
        # pyrefly: ignore [bad-assignment]
        for i, instr in enumerate(instructions):
            if instr.starts_line is not None:
                cur = instr.starts_line
            if cur != frame.f_lineno:
                continue
            if start is None:
                start = end = i
            else:
                end = i

        if start is None or end is None:  # no instructions found
            return _FrameLocalResult()

        # track involved locals and free symbols
        def go(x: Any) -> str | None:
            if isinstance(x, torch.Tensor):
                for y in x.size():
                    go(y)
                for y in x.stride():
                    go(y)
                go(x.storage_offset())
                return (
                    f"Tensor(shape: {x.size()}, "
                    f"stride: {x.stride()}, "
                    f"storage_offset: {x.storage_offset()})"
                )
            elif isinstance(x, (SymBool, SymInt, SymFloat)):
                for s in x.node.expr.free_symbols:
                    if str(s) in frame_symbols:  # type: ignore[operator]
                        continue
                    if s in self.var_to_sources:
                        frame_symbols[str(s)] = self.var_to_sources[s][0].name  # type: ignore[assignment]
                return str(x)
            return None

        # go through instructions, seeing linenos & involved locals
        last_lineno = frame.f_lineno
        for instr in instructions[start : end + 1]:
            if (lineno := instr.starts_line) is not None:
                last_lineno = max(last_lineno, lineno)
            if isinstance(instr.argval, str) and instr.argval in frame.f_locals:
                flat_locals = pytree.tree_flatten(frame.f_locals[instr.argval])[0]
                frame_locals[instr.argval] = [
                    go(flat_local) for flat_local in flat_locals
                ]

        # store LOC
        locs = co_lines[frame.f_lineno - offset : last_lineno + 1 - offset]
        if not locs:
            return _FrameLocalResult()

        indent = len(locs[0]) - len(locs[0].lstrip())
        frame_loc = "".join([loc[indent:] for loc in locs]).strip()  # type: ignore[assignment]
        return _FrameLocalResult(
            loc=frame_loc, locals=frame_locals, symbols=frame_symbols
        )