def named_item(self) -> Optional[NamedItem]:
        # named_item: NAME annotation '=' ~ item | NAME '=' ~ item | item | forced_atom | lookahead
        mark = self._mark()
        cut = False
        if (
            (name := self.name())
            and
            (annotation := self.annotation())
            and
            (literal := self.expect('='))
            and
            (cut := True)
            and
            (item := self.item())
        ):
            return NamedItem ( name . string , item , annotation )
        self._reset(mark)
        if cut: return None
        cut = False
        if (
            (name := self.name())
            and
            (literal := self.expect('='))
            and
            (cut := True)
            and
            (item := self.item())
        ):
            return NamedItem ( name . string , item )
        self._reset(mark)
        if cut: return None
        if (
            (item := self.item())
        ):
            return NamedItem ( None , item )
        self._reset(mark)
        if (
            (forced := self.forced_atom())
        ):
            return NamedItem ( None , forced )
        self._reset(mark)
        if (
            (it := self.lookahead())
        ):
            return NamedItem ( None , it )
        self._reset(mark)
        return None