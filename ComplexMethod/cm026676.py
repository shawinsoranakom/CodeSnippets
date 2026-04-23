def state(self) -> str | None:
        """Return the state."""
        if self.is_jammed:
            return LockState.JAMMED
        if self.is_opening:
            return LockState.OPENING
        if self.is_locking:
            return LockState.LOCKING
        if self.is_open:
            return LockState.OPEN
        if self.is_unlocking:
            return LockState.UNLOCKING
        if (locked := self.is_locked) is None:
            return None
        return LockState.LOCKED if locked else LockState.UNLOCKED