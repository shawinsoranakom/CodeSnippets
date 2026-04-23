def _paginate_until_error(
    git_objs: Callable[[], PaginatedList[PullRequest | Issue]],
    cursor_url: str | None,
    prev_num_objs: int,
    cursor_url_callback: Callable[[str | None, int], None],
    retrying: bool = False,
) -> Generator[PullRequest | Issue, None, None]:
    num_objs = prev_num_objs
    pag_list = git_objs()
    nextUrl_key = get_nextUrl_key(pag_list)
    if cursor_url:
        set_nextUrl(pag_list, nextUrl_key, cursor_url)
    elif retrying:
        # if we are retrying, we want to skip the objects retrieved
        # over previous calls. Unfortunately, this WILL retrieve all
        # pages before the one we are resuming from, so we really
        # don't want this case to be hit often
        logging.warning(
            "Retrying from a previous cursor-based pagination call. "
            "This will retrieve all pages before the one we are resuming from, "
            "which may take a while and consume many API calls."
        )
        pag_list = cast(PaginatedList[PullRequest | Issue], pag_list[prev_num_objs:])
        num_objs = 0

    try:
        # this for loop handles cursor-based pagination
        for issue_or_pr in pag_list:
            num_objs += 1
            yield issue_or_pr
            # used to store the current cursor url in the checkpoint. This value
            # is updated during iteration over pag_list.
            cursor_url_callback(get_nextUrl(pag_list, nextUrl_key), num_objs)

            if num_objs % CURSOR_LOG_FREQUENCY == 0:
                logging.info(
                    f"Retrieved {num_objs} objects with current cursor url: {get_nextUrl(pag_list, nextUrl_key)}"
                )

    except Exception as e:
        logging.exception(f"Error during cursor-based pagination: {e}")
        if num_objs - prev_num_objs > 0:
            raise

        if get_nextUrl(pag_list, nextUrl_key) is not None and not retrying:
            logging.info(
                "Assuming that this error is due to cursor "
                "expiration because no objects were retrieved. "
                "Retrying from the first page."
            )
            yield from _paginate_until_error(
                git_objs, None, prev_num_objs, cursor_url_callback, retrying=True
            )
            return

        # for no cursor url or if we reach this point after a retry, raise the error
        raise