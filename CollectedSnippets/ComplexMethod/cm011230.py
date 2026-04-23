def find_coalesced_group_with_non_p2p(
    pg_name: str,
    entries: list[dict[str, Any]],
    _pg_guids: dict[tuple[str, int], str],
    rank: int,
) -> list[tuple[int, dict[str, Any]]]:
    """Given a list of entries, if the collective_seq_id of the first entry matches that of subsequent ones,
    build an return a list of entries terminating in a 'coalesced' op entry all sharing a collective_seq_id
    """
    found = []
    collective_seq_id = None
    for i, e in enumerate(entries):
        if _pg_guids[(e["process_group"][0], rank)] != pg_name:
            continue
        elif collective_seq_id is None:
            collective_seq_id = (
                e["p2p_seq_id"] if e["is_p2p"] else e["collective_seq_id"]
            )
            found.append((i, e))
        elif not e["is_p2p"] and e["collective_seq_id"] == collective_seq_id:
            found.append((i, e))
        elif e["is_p2p"] and e["p2p_seq_id"] == collective_seq_id:
            found.append((i, e))
        else:
            break

    if len(found) > 1:
        name = found[-1][1]["profiling_name"]
        if name.startswith("nccl:") and not name.endswith("_coalesced"):
            logger.error("Rank %s does not have a coalesced end.", rank)
        return found
    return []