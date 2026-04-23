def _next_slot(self, stats: list[tuple[int, str]], *, update_state: bool) -> str:
        last = self._last_selected_slot
        min_active: int | None = None
        best_slot: str | None = None
        best_slot_after_last: str | None = None
        for active, slot in stats:
            if min_active is None or active < min_active:
                min_active = active
                best_slot = slot
                best_slot_after_last = None
                if last is not None and slot > last:
                    best_slot_after_last = slot
            elif active == min_active:
                if best_slot is None or slot < best_slot:
                    best_slot = slot
                if (
                    last is not None
                    and slot > last
                    and (best_slot_after_last is None or slot < best_slot_after_last)
                ):
                    best_slot_after_last = slot
        assert best_slot is not None
        slot = best_slot_after_last if best_slot_after_last is not None else best_slot
        if update_state:
            self._last_selected_slot = slot
        return slot