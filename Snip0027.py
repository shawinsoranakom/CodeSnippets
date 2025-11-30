def start_links_working_checker(links: List[str]) -> None:

    print(f'Checking if {len(links)} links are working...')

    errors = check_if_list_of_links_are_working(links)
    if errors:

        num_errors = len(errors)
        print(f'Apparently {num_errors} links are not working properly. See in:')

        for error_message in errors:
            print(error_message)

        sys.exit(1)
