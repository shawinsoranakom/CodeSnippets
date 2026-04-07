def send_log(request, exc_info):
    logger = logging.getLogger("django")
    # The default logging config has a logging filter to ensure admin emails
    # are only sent with DEBUG=False, but since someone might choose to remove
    # that filter, we still want to be able to test the behavior of error
    # emails with DEBUG=True. So we need to remove the filter temporarily.
    admin_email_handler = [
        h for h in logger.handlers if h.__class__.__name__ == "AdminEmailHandler"
    ][0]
    orig_filters = admin_email_handler.filters
    admin_email_handler.filters = []
    admin_email_handler.include_html = True
    logger.error(
        "Internal Server Error: %s",
        request.path,
        exc_info=exc_info,
        extra={"status_code": 500, "request": request},
    )
    admin_email_handler.filters = orig_filters