def func(func_method, func_url, **func_kwargs):
        """Make HTTP requests with retries and timeouts, with optional progress tracking."""
        r = None  # response
        t0 = time.time()  # initial time for timer
        for i in range(retry + 1):
            if (time.time() - t0) > timeout:
                break
            r = requests_with_progress(func_method, func_url, **func_kwargs)  # i.e. get(url, data, json, files)
            if r.status_code < 300:  # return codes in the 2xx range are generally considered "good" or "successful"
                break
            try:
                m = r.json().get("message", "No JSON message.")
            except AttributeError:
                m = "Unable to read JSON."
            if i == 0:
                if r.status_code in retry_codes:
                    m += f" Retrying {retry}x for {timeout}s." if retry else ""
                elif r.status_code == 429:  # rate limit
                    h = r.headers  # response headers
                    m = (
                        f"Rate limit reached ({h['X-RateLimit-Remaining']}/{h['X-RateLimit-Limit']}). "
                        f"Please retry after {h['Retry-After']}s."
                    )
                if verbose:
                    LOGGER.warning(f"{PREFIX}{m} {HELP_MSG} ({r.status_code} #{code})")
                if r.status_code not in retry_codes:
                    return r
            time.sleep(2**i)  # exponential standoff
        return r