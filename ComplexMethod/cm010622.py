def segsum(data):
    r"""Visually reports how the allocator has filled its segments.

    This printout can help debug fragmentation issues since free fragments
    will appear as gaps in this printout.  The amount of free space is reported
    for each segment.
    We distinguish between internal free memory which occurs because the
    allocator rounds the allocation size, and external free memory, which are
    the gaps between allocations in a segment.
    Args:
        data: snapshot dictionary created from _snapshot()
    """
    out = io.StringIO()
    out.write(f"Summary of segments >= {Bytes(PAGE_SIZE)} in size\n")
    total_reserved = 0
    total_allocated = 0
    free_external = 0
    free_internal = 0
    for seg in sorted(
        data["segments"], key=lambda x: (x["total_size"], calc_active(x))
    ):
        total_reserved += seg["total_size"]

        seg_free_external = 0
        seg_free_internal = 0
        seg_allocated = 0
        all_ranges = []
        boffset = 0
        for b in seg["blocks"]:
            active = b["state"] == "active_allocated"
            if active:
                _, allocated_size = _block_extra(b)
                all_ranges.append((boffset, allocated_size, True))
                seg_allocated += allocated_size
                seg_free_internal += b["size"] - allocated_size
            else:
                seg_free_external += b["size"]

            boffset += b["size"]

        total_allocated += seg_allocated
        free_external += seg_free_external
        free_internal += seg_free_internal

        nseg = (seg["total_size"] - 1) // PAGE_SIZE + 1
        occupied = [" " for _ in range(nseg)]
        frac = [0.0 for _ in range(nseg)]
        active_size = 0
        for i, (start_, size, active) in enumerate(all_ranges):
            active_size += size
            finish_ = start_ + size
            start = start_ // PAGE_SIZE
            finish = (finish_ - 1) // PAGE_SIZE + 1
            m = chr(ord("a" if active else "A") + (i % 26))
            for j in range(start, finish):
                s = max(start_, j * PAGE_SIZE)
                e = min(finish_, (j + 1) * PAGE_SIZE)
                frac[j] += (e - s) / PAGE_SIZE
                if occupied[j] != " ":
                    occupied[j] = "0123456789*"[int(frac[j] * 10)]
                else:
                    occupied[j] = m
        stream = "" if seg["stream"] == 0 else f", stream_{seg['stream']}"
        body = "".join(occupied)
        if seg_free_external + seg_free_internal + seg_allocated != seg["total_size"]:
            raise AssertionError(
                f"Segment size mismatch: {seg_free_external} + {seg_free_internal} + {seg_allocated} != {seg['total_size']}"
            )
        stream = f" stream_{seg['stream']}" if seg["stream"] != 0 else ""
        if seg["total_size"] >= PAGE_SIZE:
            out.write(
                f"[{body}] {Bytes(seg['total_size'])} allocated, "
                f"{_report_free(seg_free_external, seg_free_internal)} free{stream}\n"
            )
    out.write(f"segments: {len(data['segments'])}\n")
    out.write(f"total_reserved: {Bytes(total_reserved)}\n")
    out.write(f"total_allocated: {Bytes(total_allocated)}\n")
    out.write(f"total_free: {_report_free(free_external, free_internal)}\n")
    out.write(legend)
    if free_internal + free_external + total_allocated != total_reserved:
        raise AssertionError(
            f"Memory accounting error: {free_internal} + {free_external} + {total_allocated} != {total_reserved}"
        )
    return out.getvalue()