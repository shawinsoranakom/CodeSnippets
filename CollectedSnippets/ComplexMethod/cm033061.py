def _get_batch_rate_limited(
    # We pass in a callable because we want git_objs to produce a fresh
    # PaginatedList each time it's called to avoid using the same object for cursor-based pagination
    # from a partial offset-based pagination call.
    git_objs: Callable[[], PaginatedList],
    page_num: int,
    cursor_url: str | None,
    prev_num_objs: int,
    cursor_url_callback: Callable[[str | None, int], None],
    github_client: Github,
    attempt_num: int = 0,
) -> Generator[PullRequest | Issue, None, None]:
    if attempt_num > _MAX_NUM_RATE_LIMIT_RETRIES:
        raise RuntimeError(
            "Re-tried fetching batch too many times. Something is going wrong with fetching objects from Github"
        )
    try:
        if cursor_url:
            # when this is set, we are resuming from an earlier
            # cursor-based pagination call.
            yield from _paginate_until_error(
                git_objs, cursor_url, prev_num_objs, cursor_url_callback
            )
            return
        objs = list(git_objs().get_page(page_num))
        # fetch all data here to disable lazy loading later
        # this is needed to capture the rate limit exception here (if one occurs)
        for obj in objs:
            if hasattr(obj, "raw_data"):
                getattr(obj, "raw_data")
        yield from objs
    except RateLimitExceededException:
        sleep_after_rate_limit_exception(github_client)
        yield from _get_batch_rate_limited(
            git_objs,
            page_num,
            cursor_url,
            prev_num_objs,
            cursor_url_callback,
            github_client,
            attempt_num + 1,
        )
    except GithubException as e:
        if not (
            e.status == 422
            and (
                "cursor" in (e.message or "")
                or "cursor" in (e.data or {}).get("message", "")
            )
        ):
            raise
        # Fallback to a cursor-based pagination strategy
        # This can happen for "large datasets," but there's no documentation
        # On the error on the web as far as we can tell.
        # Error message:
        # "Pagination with the page parameter is not supported for large datasets,
        # please use cursor based pagination (after/before)"
        yield from _paginate_until_error(
            git_objs, cursor_url, prev_num_objs, cursor_url_callback
        )