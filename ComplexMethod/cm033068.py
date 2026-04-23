def _execute_single_retrieval(
    retrieval_function: Callable,
    continue_on_404_or_403: bool = False,
    **request_kwargs: Any,
) -> GoogleDriveFileType:
    """Execute a single retrieval from Google Drive API"""
    try:
        results = retrieval_function(**request_kwargs).execute()

    except HttpError as e:
        if e.resp.status >= 500:
            results = retrieval_function()
        elif e.resp.status == 400:
            if "pageToken" in request_kwargs and "Invalid Value" in str(e) and "pageToken" in str(e):
                logging.warning(f"Invalid page token: {request_kwargs['pageToken']}, retrying from start of request")
                request_kwargs.pop("pageToken")
                return _execute_single_retrieval(
                    retrieval_function,
                    continue_on_404_or_403,
                    **request_kwargs,
                )
            logging.error(f"Error executing request: {e}")
            raise e
        elif e.resp.status == 404 or e.resp.status == 403:
            if continue_on_404_or_403:
                logging.debug(f"Error executing request: {e}")
                results = {}
            else:
                raise e
        elif e.resp.status == 429:
            results = retrieval_function()
        else:
            logging.exception("Error executing request:")
            raise e
    except (TimeoutError, socket.timeout) as error:
        logging.warning(
            "Timed out executing Google API request; retrying with backoff. Details: %s",
            error,
        )
        results = retrieval_function()
    return results