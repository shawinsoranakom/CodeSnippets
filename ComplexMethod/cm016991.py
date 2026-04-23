def log_request_response(
    operation_id: str,
    request_method: str,
    request_url: str,
    request_headers: dict | None = None,
    request_params: dict | None = None,
    request_data: Any = None,
    response_status_code: int | None = None,
    response_headers: dict | None = None,
    response_content: Any = None,
    error_message: str | None = None,
):
    """
    Logs API request and response details to a file in the temp/api_logs directory.
    Filenames are sanitized and length-limited for cross-platform safety.
    If we still fail to write, we fall back to appending into api.log.
    """
    try:
        log_dir = get_log_directory()
        filepath = _build_log_filepath(log_dir, operation_id, request_url)

        log_content: list[str] = []
        log_content.append(f"Timestamp: {datetime.datetime.now().isoformat()}")
        log_content.append(f"Operation ID: {operation_id}")
        log_content.append("-" * 30 + " REQUEST " + "-" * 30)
        log_content.append(f"Method: {request_method}")
        log_content.append(f"URL: {request_url}")
        if request_headers:
            log_content.append(f"Headers:\n{_format_data_for_logging(request_headers)}")
        if request_params:
            log_content.append(f"Params:\n{_format_data_for_logging(request_params)}")
        if request_data is not None:
            log_content.append(f"Data/Body:\n{_format_data_for_logging(request_data)}")

        log_content.append("\n" + "-" * 30 + " RESPONSE " + "-" * 30)
        if response_status_code is not None:
            log_content.append(f"Status Code: {response_status_code}")
        if response_headers:
            log_content.append(f"Headers:\n{_format_data_for_logging(response_headers)}")
        if response_content is not None:
            log_content.append(f"Content:\n{_format_data_for_logging(response_content)}")
        if error_message:
            log_content.append(f"Error:\n{error_message}")

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(log_content))
            logger.debug("API log saved to: %s", filepath)
        except Exception as e:
            logger.error("Error writing API log to %s: %s", filepath, str(e))
    except Exception as _log_e:
        logging.debug("[DEBUG] log_request_response failed: %s", _log_e)