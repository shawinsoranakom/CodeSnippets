def lookahead(self) -> Optional[LookaheadOrCut]:
        # lookahead: '&' ~ atom | '!' ~ atom | '~'
        mark = self._mark()
        cut = False
        if (
            (literal := self.expect('&'))
            and
            (cut := True)
            and
            (atom := self.atom())
        ):
            return PositiveLookahead ( atom )
        self._reset(mark)
        if cut: return None
        cut = False
        if (
            (literal := self.expect('!'))
            and
            (cut := True)
            and
            (atom := self.atom())
        ):
            return NegativeLookahead ( atom )
        self._reset(mark)
        if cut: return None
        if (
            (literal := self.expect('~'))
        ):
            return Cut ( )
        self._reset(mark)
        return None