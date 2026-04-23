def more_alts(self) -> Optional[Rhs]:
        # more_alts: "|" alts NEWLINE more_alts | "|" alts NEWLINE
        mark = self._mark()
        if (
            (literal := self.expect("|"))
            and
            (alts := self.alts())
            and
            (_newline := self.expect('NEWLINE'))
            and
            (more_alts := self.more_alts())
        ):
            return Rhs ( alts . alts + more_alts . alts )
        self._reset(mark)
        if (
            (literal := self.expect("|"))
            and
            (alts := self.alts())
            and
            (_newline := self.expect('NEWLINE'))
        ):
            return Rhs ( alts . alts )
        self._reset(mark)
        return None