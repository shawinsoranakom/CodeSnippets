def __get__(
        self, obj: FakeTensor, objtype: type[FakeTensor] | None = None
    ) -> torch.SymInt | torch.SymFloat | None:
        if (r := getattr(obj, self._memo(obj))) is None:
            return None

        # If backed, it's ok to preserve memo since we know it won't renumber.
        if isinstance(r, torch.SymFloat) and r.node.hint is not None:
            return r

        # Version counter based tracking isn't 100% sound but it's close
        # enough
        if (
            not self._is_nested_int and getattr(obj, self._memo_vc(obj)) != obj._version
        ) or (
            not self._is_nested_int
            and getattr(obj, self._memo_epoch(obj)) != obj.fake_mode.epoch
        ):
            setattr(obj, self._memo(obj), None)
            return None
        return r