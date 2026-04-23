def item(self) -> Optional[Item]:
        # item: '[' ~ alts ']' | atom '?' | atom '*' | atom '+' | atom '.' atom '+' | atom
        mark = self._mark()
        cut = False
        if (
            (literal := self.expect('['))
            and
            (cut := True)
            and
            (alts := self.alts())
            and
            (literal_1 := self.expect(']'))
        ):
            return Opt ( alts )
        self._reset(mark)
        if cut: return None
        if (
            (atom := self.atom())
            and
            (literal := self.expect('?'))
        ):
            return Opt ( atom )
        self._reset(mark)
        if (
            (atom := self.atom())
            and
            (literal := self.expect('*'))
        ):
            return Repeat0 ( atom )
        self._reset(mark)
        if (
            (atom := self.atom())
            and
            (literal := self.expect('+'))
        ):
            return Repeat1 ( atom )
        self._reset(mark)
        if (
            (sep := self.atom())
            and
            (literal := self.expect('.'))
            and
            (node := self.atom())
            and
            (literal_1 := self.expect('+'))
        ):
            return Gather ( sep , node )
        self._reset(mark)
        if (
            (atom := self.atom())
        ):
            return atom
        self._reset(mark)
        return None