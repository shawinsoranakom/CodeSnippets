def _update_snap(
        self,
        u_type: _UpdateType,
        winfo: _WeakRefInfo,
        old_mem_consumed: int | None = None,
        old_reftype: _RefType | None = None,
    ) -> None:
        # Initialize a flag to track if the total memory might drop to zero after updates.
        maybe_zero = False
        # Ensure the device entry exists in the current memory snapshot, initializing if necessary.
        # pyrefly: ignore [no-matching-overload]
        dev_snap = self._curr_mem_snap.setdefault(
            winfo.device, dict.fromkeys(self._ref_class, 0)
        )
        dev_snap.setdefault(_TOTAL_KEY, 0)
        # Handle different types of updates based on the update type (`u_type`).
        if u_type == _UpdateType.ADD:
            # Increase the memory consumed for the specific reference type and update the total.
            dev_snap[winfo.reftype] += winfo.mem_consumed
            dev_snap[_TOTAL_KEY] += winfo.mem_consumed
        elif u_type == _UpdateType.DEL:
            # Decrease the memory consumed for the specific reference type and reduce the total.
            dev_snap[winfo.reftype] -= winfo.mem_consumed
            dev_snap[_TOTAL_KEY] -= winfo.mem_consumed
            maybe_zero = True
        elif u_type == _UpdateType.REF:
            if old_reftype is None:
                raise AssertionError
            # Adjust memory consumption between two reference types within the same device.
            dev_snap[old_reftype] -= winfo.mem_consumed
            dev_snap[winfo.reftype] += winfo.mem_consumed
        elif u_type == _UpdateType.SIZE:
            if old_mem_consumed is None:
                raise AssertionError
            # Adjust the memory consumed for a reference type due to a change in size.
            change = winfo.mem_consumed - old_mem_consumed
            dev_snap[winfo.reftype] += change
            dev_snap[_TOTAL_KEY] += change
            maybe_zero = True
        else:
            raise ValueError(f"Invalid update type: {u_type}")
        # Check if the total memory for the device has dropped to zero.
        if maybe_zero:
            if self._curr_mem_snap[winfo.device][_TOTAL_KEY] == 0:
                # Remove the device entry from the memory snapshot if the total memory is zero.
                del self._curr_mem_snap[winfo.device]