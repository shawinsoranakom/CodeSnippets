def build_groups_memberships(
    pg_config: Any,
) -> tuple[
    list[Group],
    dict[Any, Group],
    list[Membership],
    dict[str, set[Any]],
    dict[tuple[str, int], str],
]:
    """
    pg_config: {
        global_rank: {
            (pg_guid, desc, ranks)
        }
    }

    `pg_guid` is a system generated id, but depending on the mode of PG creation it could be a globally incrementing int
          or a hash of the ranks.  See `_process_group_name` in distributed_c10d.py.
    `desc` is provided by the user (optionally) and should be 'meaningful' (e.g. TP/PP/DP group)
    `ranks` is a list of the 'global ranks' that are members of the PG.

    (pg_guid, desc, ranks) tuples are appended lazily to the flight buffer when `getNCCLComm` is called on a PG and
    the `enabled_` flag is true for that PG.
        - the order of calling (init_process_group, new_group, etc) does not affect the order of the tuples in the list

    Returns:
        `groups`: a groups table where each row is a Group namedtuple.
        `_groups`: a dict that is indexed by pg_guid with Group namedtuple as value.
        `memberships`: a membership table where each row is a Membership namedtuple.
        `_memberships`: a dict that is indexed by pg_guid with set of ranks (int) as value.
        `_pg_guids`: a dict that is indexed by (pg_uid, global_rank) with pg_guid as value.
    """
    # flat lists for return
    groups = []
    memberships = []

    # dicts for faster cross-rank validation
    _groups = {}
    _memberships = {}
    _pg_guids = {}
    for global_rank in pg_config:
        for pg_uid in pg_config[global_rank]:
            desc = pg_config[global_rank][pg_uid]["desc"]
            ranks = ast.literal_eval(pg_config[global_rank][pg_uid]["ranks"])
            # With the adoption of the split_group API, we can have multiple PGs with the same pg_guid (PG Name)
            # So we need to add the hash of all its ranks within the PG as well.
            # Also guid must be a string because `_process_group_name` returns a string.
            pg_guid = pg_uid + str(hash(frozenset(ranks)))
            _pg_guids[(pg_uid, global_rank)] = pg_guid
            if isinstance(ranks, str):
                # TODO Bug in FR data format? ranks is '[0, 1,...]'
                ranks = eval(ranks)

            if pg_guid not in _groups:
                groups.append(Group(id=pg_guid, desc=desc, size=len(ranks)))
                for rank in ranks:
                    memberships.append(Membership(group_id=pg_guid, global_rank=rank))
                _groups[pg_guid] = groups[-1]
                _memberships[pg_guid] = set(ranks)
            else:
                # validation across ranks
                if _groups[pg_guid].desc != desc:
                    raise AssertionError(
                        f"mismatch in desc {_groups[pg_guid].desc} vs {desc} for group {pg_guid}"
                    )
                if _memberships[pg_guid] != set(ranks):
                    raise AssertionError(
                        f"mismatch in membership for group {pg_guid}"
                        f" {_memberships[pg_guid]} vs {set(ranks)}"
                    )
    return groups, _groups, memberships, _memberships, _pg_guids