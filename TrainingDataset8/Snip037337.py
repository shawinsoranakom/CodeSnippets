def _main_dg(self) -> "DeltaGenerator":
        """Return this DeltaGenerator's root - that is, the top-level ancestor
        DeltaGenerator that we belong to (this generally means the st._main
        DeltaGenerator).
        """
        return self._parent._main_dg if self._parent else self