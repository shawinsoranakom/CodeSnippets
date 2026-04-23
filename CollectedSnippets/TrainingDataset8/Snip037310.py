def props(self) -> Any:
        """Other data in this cursor. This is a temporary measure that will go
        away when we implement improved return values for elements.

        This is only implemented in LockedCursor.
        """
        raise NotImplementedError()