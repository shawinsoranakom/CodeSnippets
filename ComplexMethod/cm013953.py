def __ior__(self, other: Self) -> Self:
        # Record current static sizes before merge. For dims that become
        # dynamic, the exclusion guard will reject these values so inputs
        # fall through to the earlier, more specialized cache entry.
        # Already-dynamic dims become None and are ignored by the guard.
        # When no dim transitions, clear stale excluded_sizes so later
        # compilations don't inherit exclusions from earlier transitions.
        new_size = self._merge_atom_tup(self.size, other.size)
        if isinstance(self.size, tuple):
            if new_size != self.size:
                self.excluded_sizes = tuple(
                    s if type(s) is int else None for s in self.size
                )
            elif self.excluded_sizes is not None:
                self.excluded_sizes = None
        self.size = new_size
        # Same idea for scalars: record the static value about to become dynamic.
        # Re-derive like excluded_sizes: only set when transitioning from a
        # concrete int, clear when already dynamic.
        if (
            type(self.scalar) is int
            and type(other.scalar) is int
            and self.scalar != other.scalar
        ):
            self.excluded_scalar = self.scalar
        elif self.scalar is auto_dynamic and self.excluded_scalar is not None:
            self.excluded_scalar = None
        self.scalar = self._merge_atom(self.scalar, other.scalar)
        self.stride = self._merge_atom_tup(self.stride, other.stride)
        return self