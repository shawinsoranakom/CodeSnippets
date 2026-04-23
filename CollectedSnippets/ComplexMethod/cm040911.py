def s3_cors_request_handler(chain: HandlerChain, context: RequestContext, response: Response):
    """
    Handler to add default CORS headers to S3 operations not concerned with CORS configuration
    """
    # if DISABLE_CUSTOM_CORS_S3 is true, the default CORS handling will take place, so we won't need to do it here
    if config.DISABLE_CUSTOM_CORS_S3:
        return

    if not context.service or context.service.service_name != "s3":
        return

    if not context.operation or context.operation.name not in ("ListBuckets", "CreateBucket"):
        return

    if not config.DISABLE_CORS_CHECKS and not is_origin_allowed_default(context.request.headers):
        LOG.info(
            "Blocked CORS request from forbidden origin %s",
            context.request.headers.get("origin") or context.request.headers.get("referer"),
        )
        response.status_code = 403
        chain.terminate()

    add_default_headers(response_headers=response.headers, request_headers=context.request.headers)