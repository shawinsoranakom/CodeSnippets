def target_atom(self) -> Optional[str]:
        # target_atom: "{" ~ target_atoms? "}" | "[" ~ target_atoms? "]" | NAME "*" | NAME | NUMBER | STRING | FSTRING_START | FSTRING_MIDDLE | FSTRING_END | "?" | ":" | !"}" !"]" OP
        mark = self._mark()
        cut = False
        if (
            (literal := self.expect("{"))
            and
            (cut := True)
            and
            (atoms := self.target_atoms(),)
            and
            (literal_1 := self.expect("}"))
        ):
            return "{" + ( atoms or "" ) + "}"
        self._reset(mark)
        if cut: return None
        cut = False
        if (
            (literal := self.expect("["))
            and
            (cut := True)
            and
            (atoms := self.target_atoms(),)
            and
            (literal_1 := self.expect("]"))
        ):
            return "[" + ( atoms or "" ) + "]"
        self._reset(mark)
        if cut: return None
        if (
            (name := self.name())
            and
            (literal := self.expect("*"))
        ):
            return name . string + "*"
        self._reset(mark)
        if (
            (name := self.name())
        ):
            return name . string
        self._reset(mark)
        if (
            (number := self.number())
        ):
            return number . string
        self._reset(mark)
        if (
            (string := self.string())
        ):
            return string . string
        self._reset(mark)
        if (
            (fstring_start := self.fstring_start())
        ):
            return fstring_start . string
        self._reset(mark)
        if (
            (fstring_middle := self.fstring_middle())
        ):
            return fstring_middle . string
        self._reset(mark)
        if (
            (fstring_end := self.fstring_end())
        ):
            return fstring_end . string
        self._reset(mark)
        if (
            (literal := self.expect("?"))
        ):
            return "?"
        self._reset(mark)
        if (
            (literal := self.expect(":"))
        ):
            return ":"
        self._reset(mark)
        if (
            self.negative_lookahead(self.expect, "}")
            and
            self.negative_lookahead(self.expect, "]")
            and
            (op := self.op())
        ):
            return op . string
        self._reset(mark)
        return None