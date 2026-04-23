def _find_pg_by_ranks_and_tag(tag: str, ranks: list[int]) -> ProcessGroup | None:
    if len(tag) > 0 and not tag.startswith("ptd:") and not tag.startswith("user:"):
        tag = f"user:{tag}"

    for group in _world.tags_to_pg.get(tag, []):
        if group.size() != len(ranks):
            continue

        group_ranks = get_process_group_ranks(group)
        good = all(r in group_ranks for r in ranks)
        if good:
            return group
    return None