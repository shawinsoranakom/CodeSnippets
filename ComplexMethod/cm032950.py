def _handle_http_error(e: requests.HTTPError, attempt: int) -> int:
    MIN_DELAY = 2
    MAX_DELAY = 60
    STARTING_DELAY = 5
    BACKOFF = 2

    # Check if the response or headers are None to avoid potential AttributeError
    if e.response is None or e.response.headers is None:
        logging.warning("HTTPError with `None` as response or as headers")
        raise e

    # Confluence Server returns 403 when rate limited
    if e.response.status_code == 403:
        FORBIDDEN_MAX_RETRY_ATTEMPTS = 7
        FORBIDDEN_RETRY_DELAY = 10
        if attempt < FORBIDDEN_MAX_RETRY_ATTEMPTS:
            logging.warning(f"403 error. This sometimes happens when we hit Confluence rate limits. Retrying in {FORBIDDEN_RETRY_DELAY} seconds...")
            return FORBIDDEN_RETRY_DELAY

        raise e

    if e.response.status_code != 429 and RATE_LIMIT_MESSAGE_LOWERCASE not in e.response.text.lower():
        raise e

    retry_after = None

    retry_after_header = e.response.headers.get("Retry-After")
    if retry_after_header is not None:
        try:
            retry_after = int(retry_after_header)
            if retry_after > MAX_DELAY:
                logging.warning(f"Clamping retry_after from {retry_after} to {MAX_DELAY} seconds...")
                retry_after = MAX_DELAY
            if retry_after < MIN_DELAY:
                retry_after = MIN_DELAY
        except ValueError:
            pass

    if retry_after is not None:
        logging.warning(f"Rate limiting with retry header. Retrying after {retry_after} seconds...")
        delay = retry_after
    else:
        logging.warning("Rate limiting without retry header. Retrying with exponential backoff...")
        delay = min(STARTING_DELAY * (BACKOFF**attempt), MAX_DELAY)

    delay_until = math.ceil(time.monotonic() + delay)
    return delay_until