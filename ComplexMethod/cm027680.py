def migrate_project_keys_translations(from_project_id, to_project_id, to_migrate):
    """Migrate keys and translations from one project to another.

    to_migrate is Dict[from_key] = to_key.
    """
    from_lokalise = get_api(from_project_id)
    to_lokalise = get_api(to_project_id)

    # Fetch keys in target
    # We are going to skip migrating existing keys
    print("Checking which target keys exist..")
    try:
        to_key_data = list_keys_helper(
            to_lokalise, list(to_migrate.values()), validate=False
        )
    except ValueError:
        return

    existing = set(create_lookup(to_key_data))

    missing = [key for key in to_migrate.values() if key not in existing]

    if not missing:
        print("All keys to migrate exist already, nothing to do")
        return

    # Fetch keys whose translations we're importing
    print("Fetch translations that we're importing..")
    try:
        from_key_data = list_keys_helper(
            from_lokalise,
            [key for key, value in to_migrate.items() if value not in existing],
            {"include_translations": 1},
        )
    except ValueError:
        return

    from_key_lookup = create_lookup(from_key_data)

    print("Creating", ", ".join(missing))
    to_key_lookup = create_lookup(
        to_lokalise.keys_create(
            [{"key_name": key, "platforms": ["web"]} for key in missing]
        )
    )

    updates = []

    for from_key, to_key in to_migrate.items():
        # If it is not in lookup, it already existed, skipping it.
        if to_key not in to_key_lookup:
            continue

        updates.append(
            {
                "key_id": to_key_lookup[to_key]["key_id"],
                "translations": [
                    {
                        "language_iso": from_translation["language_iso"],
                        "translation": from_translation["translation"],
                        "is_reviewed": from_translation["is_reviewed"],
                        "is_fuzzy": from_translation["is_fuzzy"],
                    }
                    for from_translation in from_key_lookup[from_key]["translations"]
                ],
            }
        )

    print("Updating")
    pprint(updates)
    print()
    print()
    pprint(to_lokalise.keys_bulk_update(updates))