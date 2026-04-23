def merge_contiguous_blocks(
        self,
        offsets_local: list[int],
        offsets_remote: list[int],
        sizes: list[int],
        assume_sorted: bool = False,
    ) -> tuple[list[int], list[int], list[int]]:
        n = len(offsets_local)
        if n == 0:
            return [], [], []
        if not (n == len(offsets_remote) == len(sizes)):
            raise ValueError("Input list lengths mismatch")
        local_arr = np.fromiter(offsets_local, dtype=np.int64, count=n)
        remote_arr = np.fromiter(offsets_remote, dtype=np.int64, count=n)
        sizes_arr = np.fromiter(sizes, dtype=np.int64, count=n)

        if assume_sorted:
            local_sorted = local_arr
            remote_sorted = remote_arr
            sizes_sorted = sizes_arr
        else:
            if np.all(local_arr[:-1] <= local_arr[1:]):
                local_sorted = local_arr
                remote_sorted = remote_arr
                sizes_sorted = sizes_arr
            else:
                sort_idx = np.argsort(local_arr, kind="stable")
                local_sorted = local_arr[sort_idx]
                remote_sorted = remote_arr[sort_idx]
                sizes_sorted = sizes_arr[sort_idx]

        if n == 1:
            return (
                [int(local_sorted[0])],
                [int(remote_sorted[0])],
                [int(sizes_sorted[0])],
            )

        diff_local = local_sorted[1:] - local_sorted[:-1]
        diff_remote = remote_sorted[1:] - remote_sorted[:-1]
        prev_size = sizes_sorted[:-1]

        contiguous = (diff_local == prev_size) & (diff_remote == prev_size)

        if not contiguous.any():
            return local_sorted.tolist(), remote_sorted.tolist(), sizes_sorted.tolist()

        if contiguous.all():
            total_size = int(sizes_sorted.sum())
            return [int(local_sorted[0])], [int(remote_sorted[0])], [total_size]

        break_positions = np.flatnonzero(~contiguous) + 1
        segment_starts = np.concatenate(([0], break_positions))
        segment_ends = np.concatenate((break_positions, [n]))

        seg_count = len(segment_starts)
        merged_local = [0] * seg_count
        merged_remote = [0] * seg_count
        merged_sizes = [0] * seg_count

        for si in range(seg_count):
            s = segment_starts[si]
            e = segment_ends[si]
            merged_local[si] = int(local_sorted[s])
            merged_remote[si] = int(remote_sorted[s])

            merged_sizes[si] = int(
                local_sorted[e - 1] + sizes_sorted[e - 1] - local_sorted[s]
            )

        return merged_local, merged_remote, merged_sizes