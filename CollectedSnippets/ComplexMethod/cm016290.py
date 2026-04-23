def _update_registry_with_changes(
    registry: dict,
    calls: dict[str, tuple[dict[str, Any], Path]],
    renames: dict[str, str] | None = None,
) -> dict:
    """Calculate what the updated registry should look like."""
    renames = renames or {}
    updated_registry = dict(registry)

    latest_entry: dict[str, Any] = {
        entries[0]["Gb_type"]: entries[0] for entries in registry.values()
    }
    gb_type_to_key: dict[str, str] = {
        entries[0]["Gb_type"]: key for key, entries in registry.items()
    }

    # Method for determining add vs. update:
    # - If gb_type exists in registry but content differs: UPDATE (append new entry to preserve history)
    # - If gb_type is new but content matches existing entry: RENAME (append new entry with new gb_type)
    # - If gb_type is completely new: ADD (create new registry entry with a new GBID)

    for old_gb_type, new_gb_type in renames.items():
        registry_key = gb_type_to_key[old_gb_type]
        old_entry = updated_registry[registry_key][0]

        new_entry = _create_registry_entry(
            new_gb_type,
            old_entry["Context"],
            old_entry["Explanation"],
            old_entry["Hints"],
        )
        updated_registry[registry_key] = [new_entry] + updated_registry[registry_key]

        latest_entry[new_gb_type] = new_entry
        gb_type_to_key[new_gb_type] = registry_key
        del latest_entry[old_gb_type]
        del gb_type_to_key[old_gb_type]

    # Collect new entries separately to insert them all at once
    new_entries: list[tuple[str, list[dict[str, Any]]]] = []

    for gb_type, (call, file_path) in calls.items():
        if gb_type in latest_entry:
            existing_entry = latest_entry[gb_type]

            if not (
                call["context"] == existing_entry["Context"]
                and call["explanation"] == existing_entry["Explanation"]
                and sorted(call["hints"]) == sorted(existing_entry["Hints"])
            ):
                registry_key = gb_type_to_key[gb_type]
                new_entry = _create_registry_entry(
                    gb_type, call["context"], call["explanation"], call["hints"]
                )
                updated_registry[registry_key] = [new_entry] + updated_registry[
                    registry_key
                ]
        else:
            # Collect new entries to add later
            new_key = next_gb_id(updated_registry)
            new_entry = _create_registry_entry(
                gb_type, call["context"], call["explanation"], call["hints"]
            )
            new_entries.append((new_key, [new_entry]))
            # Temporarily add to updated_registry so next_gb_id works correctly
            updated_registry[new_key] = [new_entry]

    # Insert all new entries at the same random position to reduce merge conflicts
    if new_entries:
        # Remove temporarily added entries
        for new_key, _ in new_entries:
            del updated_registry[new_key]

        registry_items = list(updated_registry.items())
        if registry_items:
            # Pick one random position for all new entries
            insert_pos = random.randint(0, len(registry_items))
            # Insert all new entries at the same position
            for new_key, new_entry in new_entries:
                registry_items.insert(insert_pos, (new_key, new_entry))
                insert_pos += 1  # Keep them together
            updated_registry = dict(registry_items)
        else:
            # Empty registry, just add all entries
            for new_key, new_entry in new_entries:
                updated_registry[new_key] = new_entry

    return updated_registry