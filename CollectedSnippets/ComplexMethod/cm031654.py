def meta(self) -> Optional[MetaTuple]:
        # meta: "@" NAME NEWLINE | "@" NAME NAME NEWLINE | "@" NAME STRING NEWLINE
        mark = self._mark()
        if (
            (literal := self.expect("@"))
            and
            (name := self.name())
            and
            (_newline := self.expect('NEWLINE'))
        ):
            return ( name . string , None )
        self._reset(mark)
        if (
            (literal := self.expect("@"))
            and
            (a := self.name())
            and
            (b := self.name())
            and
            (_newline := self.expect('NEWLINE'))
        ):
            return ( a . string , b . string )
        self._reset(mark)
        if (
            (literal := self.expect("@"))
            and
            (name := self.name())
            and
            (string := self.string())
            and
            (_newline := self.expect('NEWLINE'))
        ):
            return ( name . string , literal_eval ( string . string ) )
        self._reset(mark)
        return None