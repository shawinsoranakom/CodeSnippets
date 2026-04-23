def run():
    """Clean translations."""
    args = get_arguments()
    if args.target == "frontend":
        missing_keys = find_frontend()
        lokalise = get_api(FRONTEND_PROJECT_ID)
    else:
        missing_keys = find_core()
        lokalise = get_api(CORE_PROJECT_ID)

    if not missing_keys:
        print("No missing translations!")
        return 0

    print(f"Found {len(missing_keys)} extra keys")

    # We can't query too many keys at once, so limit the number to 50.
    for i in range(0, len(missing_keys), 50):
        chunk = missing_keys[i : i + 50]

        key_data = lokalise.keys_list({"filter_keys": ",".join(chunk), "limit": 1000})
        if len(key_data) != len(chunk):
            print(
                f"Looking up key in Lokalise returns {len(key_data)} results, expected {len(chunk)}"
            )

        if not key_data:
            continue

        print(f"Deleting {len(key_data)} keys:")
        for key in key_data:
            print(" -", key["key_name"]["web"])
        print()
        while input("Type YES to delete these keys: ") != "YES":
            pass

        print(lokalise.keys_delete_multiple([key["key_id"] for key in key_data]))
        print()

    return 0