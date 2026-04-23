def _filter_sqlite_noise(diffs: list) -> list:
    """Filter out diffs that are known SQLite limitations.

    - modify_nullable: SQLite doesn't support ALTER COLUMN
    - remove_fk/add_fk: SQLite doesn't track FK constraint names or actions
      (ondelete/onupdate), so autogenerate sees phantom FK diffs. Paired
      remove/add on the same (table, columns) with identical referenced targets
      are suppressed; unpaired or re-targeted FKs are preserved.
    """
    significant_diffs = []
    fk_removes: dict = {}  # (table, col_tuple) -> ForeignKeyConstraint
    fk_adds: dict = {}

    for d in diffs:
        if not (isinstance(d, tuple) and len(d) >= 2):
            significant_diffs.append(d)
            continue

        op_type = d[0]
        if op_type == "modify_nullable":
            continue
        if op_type in ("remove_fk", "add_fk"):
            fk = d[1]
            try:
                key = (fk.parent.name, tuple(sorted(c.name for c in fk.columns)))
            except (AttributeError, TypeError):
                significant_diffs.append(d)
                continue
            if op_type == "remove_fk":
                fk_removes[key] = fk
            else:
                fk_adds[key] = fk
            continue

        significant_diffs.append(d)

    # Compare FK remove/add pairs: suppress when referenced targets match.
    # We intentionally skip ondelete/onupdate comparison because SQLite's
    # PRAGMA foreign_key_list does not reliably report these actions.
    all_fk_keys = set(fk_removes) | set(fk_adds)
    for key in all_fk_keys:
        rm = fk_removes.get(key)
        add = fk_adds.get(key)
        if rm and add:
            rm_targets = sorted(
                (elem.column.table.name, elem.column.name) for elem in rm.elements if elem.column is not None
            )
            add_targets = sorted(
                (elem.column.table.name, elem.column.name) for elem in add.elements if elem.column is not None
            )
            if rm_targets and rm_targets == add_targets:
                continue  # Same target — name-only or action-only diff is SQLite noise
        if rm:
            significant_diffs.append(("remove_fk", rm))
        if add:
            significant_diffs.append(("add_fk", add))

    return significant_diffs