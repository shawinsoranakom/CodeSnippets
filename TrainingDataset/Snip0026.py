def start_duplicate_links_checker(links: List[str]) -> None:

    print('Checking for duplicate links...')

    has_duplicate_link, duplicates_links = check_duplicate_links(links)

    if has_duplicate_link:
        print(f'Found duplicate links:')

        for duplicate_link in duplicates_links:
            print(duplicate_link)

        sys.exit(1)
    else:
        print('No duplicate links.')
