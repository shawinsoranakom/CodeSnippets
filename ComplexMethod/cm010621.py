def compare(before, after, format_flamegraph=format_flamegraph):
    def _seg_key(seg):
        return (seg["address"], seg["total_size"])

    def _seg_info(seg):
        return f"stream_{seg['stream']};seg_{seg['address']}"

    f = io.StringIO()

    before_segs = {_seg_key(seg) for seg in before}
    after_segs = {_seg_key(seg) for seg in after}

    print(f"only_before = {[a for a, _ in (before_segs - after_segs)]}")
    print(f"only_after = {[a for a, _ in (after_segs - before_segs)]}")

    for seg in before:
        if _seg_key(seg) not in after_segs:
            _write_blocks(f, f"only_before;{_seg_info(seg)}", seg["blocks"])

    for seg in after:
        if _seg_key(seg) not in before_segs:
            _write_blocks(f, f"only_after;{_seg_info(seg)}", seg["blocks"])

    return format_flamegraph(f.getvalue())