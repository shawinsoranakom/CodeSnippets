def build_mfr_batch_groups(sorted_areas: list[int], requested_batch_size: int) -> list[list[int]]:
    if not sorted_areas:
        return []

    total_count = len(sorted_areas)
    effective_batch_size = get_mfr_effective_batch_size(
        total_count,
        requested_batch_size,
    )
    if effective_batch_size < 1:
        return []

    min_dynamic_batch_size = get_mfr_min_dynamic_batch_size(requested_batch_size)
    batch_groups = []
    if total_count < min_dynamic_batch_size:
        batch_groups.append(list(range(total_count)))
        return finalize_mfr_batch_groups(
            batch_groups,
            total_count,
            requested_batch_size,
        )

    base_mean_area = sum(sorted_areas[:effective_batch_size]) / effective_batch_size
    cursor = 0

    while cursor < total_count:
        remaining_count = total_count - cursor
        if remaining_count < min_dynamic_batch_size:
            batch_groups.append(list(range(cursor, total_count)))
            break

        probe_size = min(effective_batch_size, remaining_count)
        current_mean_area = sum(sorted_areas[cursor : cursor + probe_size]) / probe_size
        ratio = 1 if base_mean_area <= 0 else current_mean_area / base_mean_area

        candidate_batch_size = effective_batch_size
        threshold = 4
        while (
            ratio >= threshold
            and candidate_batch_size // 2 >= min_dynamic_batch_size
        ):
            candidate_batch_size //= 2
            threshold *= 2

        candidate_batch_size = min(
            candidate_batch_size,
            largest_power_of_two_leq(remaining_count),
        )
        batch_groups.append(list(range(cursor, cursor + candidate_batch_size)))
        cursor += candidate_batch_size

    return finalize_mfr_batch_groups(
        batch_groups,
        total_count,
        requested_batch_size,
    )