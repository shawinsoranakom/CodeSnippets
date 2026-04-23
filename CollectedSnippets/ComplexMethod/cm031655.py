def rule(self) -> Optional[Rule]:
        # rule: rulename flags? ":" alts NEWLINE INDENT more_alts DEDENT | rulename flags? ":" NEWLINE INDENT more_alts DEDENT | rulename flags? ":" alts NEWLINE
        mark = self._mark()
        if (
            (rulename := self.rulename())
            and
            (flags := self.flags(),)
            and
            (literal := self.expect(":"))
            and
            (alts := self.alts())
            and
            (_newline := self.expect('NEWLINE'))
            and
            (_indent := self.expect('INDENT'))
            and
            (more_alts := self.more_alts())
            and
            (_dedent := self.expect('DEDENT'))
        ):
            return Rule ( rulename [0] , rulename [1] , Rhs ( alts . alts + more_alts . alts ) , flags = flags )
        self._reset(mark)
        if (
            (rulename := self.rulename())
            and
            (flags := self.flags(),)
            and
            (literal := self.expect(":"))
            and
            (_newline := self.expect('NEWLINE'))
            and
            (_indent := self.expect('INDENT'))
            and
            (more_alts := self.more_alts())
            and
            (_dedent := self.expect('DEDENT'))
        ):
            return Rule ( rulename [0] , rulename [1] , more_alts , flags = flags )
        self._reset(mark)
        if (
            (rulename := self.rulename())
            and
            (flags := self.flags(),)
            and
            (literal := self.expect(":"))
            and
            (alts := self.alts())
            and
            (_newline := self.expect('NEWLINE'))
        ):
            return Rule ( rulename [0] , rulename [1] , alts , flags = flags )
        self._reset(mark)
        return None