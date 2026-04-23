def alt(self) -> Optional[Alt]:
        # alt: items '$' action | items '$' | items action | items
        mark = self._mark()
        if (
            (items := self.items())
            and
            (literal := self.expect('$'))
            and
            (action := self.action())
        ):
            return Alt ( items + [NamedItem ( None , NameLeaf ( 'ENDMARKER' ) )] , action = action )
        self._reset(mark)
        if (
            (items := self.items())
            and
            (literal := self.expect('$'))
        ):
            return Alt ( items + [NamedItem ( None , NameLeaf ( 'ENDMARKER' ) )] , action = None )
        self._reset(mark)
        if (
            (items := self.items())
            and
            (action := self.action())
        ):
            return Alt ( items , action = action )
        self._reset(mark)
        if (
            (items := self.items())
        ):
            return Alt ( items , action = None )
        self._reset(mark)
        return None