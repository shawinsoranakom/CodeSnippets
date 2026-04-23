def atom(self) -> Optional[Plain]:
        # atom: '(' ~ alts ')' | NAME | STRING
        mark = self._mark()
        cut = False
        if (
            (literal := self.expect('('))
            and
            (cut := True)
            and
            (alts := self.alts())
            and
            (literal_1 := self.expect(')'))
        ):
            return Group ( alts )
        self._reset(mark)
        if cut: return None
        if (
            (name := self.name())
        ):
            return NameLeaf ( name . string )
        self._reset(mark)
        if (
            (string := self.string())
        ):
            return StringLeaf ( string . string )
        self._reset(mark)
        return None