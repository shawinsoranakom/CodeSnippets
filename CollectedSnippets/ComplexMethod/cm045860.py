def finalize_mfr_batch_groups(
    batch_groups: list[list[int]],
    total_count: int,
    requested_batch_size: int,
) -> list[list[int]]:
    if not batch_groups:
        return []

    if len(batch_groups) == 1:
        if total_count <= 1 or requested_batch_size <= total_count:
            return batch_groups

        first_group_size = largest_power_of_two_leq(total_count - 1)
        if first_group_size < 1:
            return batch_groups

        source_group = batch_groups[0]
        first_group = source_group[:first_group_size]
        second_group = source_group[first_group_size:]
        if not first_group or not second_group:
            return batch_groups
        return [first_group, second_group]

    while (
        len(batch_groups) >= 3
        and len(batch_groups[-1]) < len(batch_groups[-2])
    ):
        tail_group = batch_groups.pop()
        batch_groups[-1].extend(tail_group)

    return batch_groups